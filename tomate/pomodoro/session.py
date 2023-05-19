from __future__ import annotations

import enum
import logging
import uuid
from collections import namedtuple

from wiring import SingletonScope, inject
from wiring.scanning import register

from .event import Bus, Events, Subscriber, on
from .fsm import fsm
from .timer import Payload as TimerPayload, SECONDS_IN_A_MINUTE, Timer, format_seconds
from .config import Config, Payload as ConfigPayload

logger = logging.getLogger(__name__)


class Payload(namedtuple("SessionPayload", ["id", "type", "pomodoros", "duration"])):
    @property
    def countdown(self) -> str:
        return format_seconds(self.duration)


class Type(enum.Enum):
    POMODORO = 0
    SHORT_BREAK = 1
    LONG_BREAK = 2

    @classmethod
    def of(cls, index) -> Type:
        for number, attr in enumerate(cls):
            if number == index:
                return attr

    @property
    def option(self) -> str:
        return "{}_duration".format(self.name.replace("_", "").lower())


@enum.unique
class State(enum.Enum):
    INITIAL = 0
    STOPPED = 1
    STARTED = 2
    ENDED = 3


@register.factory("tomate.session", scope=SingletonScope)
class Session(Subscriber):
    @inject(
        bus="tomate.bus",
        config="tomate.config",
        timer="tomate.timer",
    )
    def __init__(self, bus: Bus, config: Config, timer: Timer):
        self._config = config
        self._timer = timer
        self._bus = bus
        self.state = State.INITIAL
        self.current = Type.POMODORO
        self.pomodoros = 0
        self.connect(bus)

    @fsm(source=[State.INITIAL], target=State.STOPPED, exit=lambda self: self._trigger(Events.SESSION_READY))
    def ready(self) -> None:
        pass

    @fsm(
        source=[State.STOPPED, State.ENDED], target=State.STARTED, exit=lambda self: self._trigger(Events.SESSION_START)
    )
    def start(self) -> bool:
        logger.debug("action=start")
        self._timer.start(self.duration)
        return True

    def is_running(self) -> bool:
        return self._timer.is_running()

    @fsm(
        source=[State.STARTED],
        target=State.STOPPED,
        condition=is_running,
        exit=lambda self: self._trigger(Events.SESSION_INTERRUPT),
    )
    def stop(self) -> bool:
        logger.debug("action=stop")
        self._timer.stop()
        return True

    @fsm(source=[State.STOPPED, State.ENDED], target="self", exit=lambda self: self._trigger(Events.SESSION_RESET))
    def reset(self) -> bool:
        logger.debug("action=reset")
        self.pomodoros = 0
        return True

    @on(Events.CONFIG_CHANGE)
    def _on_config_change(self, payload: ConfigPayload) -> bool:
        if payload.section != "timer":
            return False

        return self.change(self.current)

    @fsm(source=[State.STOPPED, State.ENDED], target="self", exit=lambda self: self._trigger(Events.SESSION_CHANGE))
    def change(self, session: Type) -> bool:
        logger.debug("action=change current=%s next=%s", self.current, session)
        self.current = session
        return True

    @property
    def duration(self) -> int:
        minutes = self._config.get_int(self._config.DURATION_SECTION, self.current.option)
        return int(minutes * SECONDS_IN_A_MINUTE)

    def timer_is_up(self) -> bool:
        return not self._timer.is_running()

    @on(Events.TIMER_END)
    @fsm(
        source=[State.STARTED],
        target=State.ENDED,
        condition=timer_is_up,
        exit=lambda self: self._trigger(Events.SESSION_CHANGE),
    )
    def _end(self, payload: TimerPayload) -> bool:
        payload = self._create_payload(duration=payload.duration)

        if self.current == Type.POMODORO:
            self.pomodoros += 1
            self.current = self._choose_break()
        else:
            self.current = Type.POMODORO

        logger.debug("action=end previous=%s current=%s", payload.type, self.current)

        self.state = State.ENDED
        self._bus.send(Events.SESSION_END, payload=payload._replace(pomodoros=self.pomodoros))

        return True

    def _choose_break(self):
        return Type.LONG_BREAK if self._is_long_break() else Type.SHORT_BREAK

    def _is_long_break(self) -> bool:
        long_break_interval = self._config.get_int(self._config.DURATION_SECTION, "long_break_interval")
        return not self.pomodoros % long_break_interval

    def _trigger(self, event: Events) -> None:
        self._bus.send(event, payload=self._create_payload())

    def _create_payload(self, **kwargs) -> Payload:
        defaults = {
            "duration": self.duration,
            "id": uuid.uuid4(),
            "pomodoros": self.pomodoros,
            "type": self.current,
        }
        defaults.update(kwargs)
        return Payload(**defaults)
