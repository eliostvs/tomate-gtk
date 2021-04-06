import enum
import logging
from collections import namedtuple

import blinker
from gi.repository import GLib
from wiring import SingletonScope, inject
from wiring.scanning import register

from .event import Events
from .fsm import fsm

logger = logging.getLogger(__name__)
SECONDS_IN_A_MINUTE = 60


class Payload(namedtuple("TimerPayload", "time_left duration")):
    __slots__ = ()

    @property
    def remaining_ratio(self) -> float:
        try:
            return self.time_left / self.duration
        except ZeroDivisionError:
            return 0.0

    @property
    def elapsed_ratio(self) -> float:
        return round(1.0 - self.remaining_ratio, 1)

    @property
    def elapsed_percent(self):
        """
        Returns the percentage in 5% steps
        """
        percent = self.elapsed_ratio * 100
        return percent - percent % 5


# Based on Tomatoro create by Pierre Quillery.
# https://github.com/dandelionmood/Tomatoro
# Thanks Pierre!


class State(enum.Enum):
    STOPPED = 1
    STARTED = 2
    ENDED = 3


@register.factory("tomate.timer", scope=SingletonScope)
class Timer:
    ONE_SECOND = 1

    @inject(bus="tomate.bus")
    def __init__(self, bus: blinker.Signal):
        self.duration = self.time_left = 0
        self.state = State.STOPPED
        self._bus = bus

    @fsm(target=State.STARTED, source=[State.ENDED, State.STOPPED], exit=lambda self: self._trigger(Events.TIMER_START))
    def start(self, seconds: int) -> bool:
        logger.debug("action=start")
        self.duration = self.time_left = seconds
        GLib.timeout_add_seconds(Timer.ONE_SECOND, self._update)
        return True

    @fsm(target=State.STOPPED, source=[State.STARTED], exit=lambda self: self._trigger(Events.TIMER_STOP))
    def stop(self) -> bool:
        logger.debug("action=reset")
        self._reset()
        return True

    def _is_up(self) -> bool:
        return self.time_left <= 0

    def is_running(self) -> bool:
        return self.state == State.STARTED

    @fsm(
        target=State.ENDED, source=[State.STARTED], condition=_is_up, exit=lambda self: self._trigger(Events.TIMER_END)
    )
    def end(self) -> bool:
        logger.debug("action=end")
        return True

    def _update(self) -> bool:
        logger.debug("action=update time_left=%d duration=%d", self.time_left, self.duration)

        if self.state != State.STARTED:
            return False

        if self._is_up():
            return self.end()

        self.time_left -= 1
        self._trigger(Events.TIMER_UPDATE)
        return True

    def _reset(self) -> None:
        self.duration = self.time_left = 0

    def _trigger(self, event) -> None:
        self._bus.send(event, payload=Payload(time_left=self.time_left, duration=self.duration))


def format_time_left(seconds: int) -> str:
    minutes, seconds = divmod(seconds, SECONDS_IN_A_MINUTE)
    return "{0:0>2}:{1:0>2}".format(minutes, seconds)
