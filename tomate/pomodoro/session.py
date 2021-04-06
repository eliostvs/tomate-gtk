from __future__ import annotations

import enum
import uuid
from collections import namedtuple

from blinker import Signal
from wiring import SingletonScope, inject
from wiring.scanning import register

from .event import Bus, Events, Subscriber, on
from .fsm import fsm
from .timer import Payload as TimerPayload, SECONDS_IN_A_MINUTE, Timer

Payload = namedtuple("SessionPayload", "id type pomodoros duration")
EndPayload = namedtuple("SessionEndPayload", "id type pomodoros duration previous")


class Type(enum.Enum):
    POMODORO = 0
    SHORT_BREAK = 1
    LONG_BREAK = 2

    @classmethod
    def of(cls, index) -> Type:
        for (number, attr) in enumerate(cls):
            if number == index:
                return attr

    @property
    def option(self) -> str:
        return "{}_duration".format(self.name.replace("_", "").lower())


class State(enum.Enum):
    STOPPED = 1
    STARTED = 2
    ENDED = 3


@register.factory("tomate.session", scope=SingletonScope)
class Session(Subscriber):
    @inject(timer="tomate.timer", config="tomate.config", bus="tomate.bus")
    def __init__(self, timer: Timer, config, bus: Signal):
        self._config = config
        self._timer = timer
        self._bus = bus
        self.state = State.STOPPED
        self.current = Type.POMODORO
        self.pomodoros = 0

    @fsm(
        source=[State.STOPPED, State.ENDED], target=State.STARTED, exit=lambda self: self._trigger(Events.SESSION_START)
    )
    def start(self) -> bool:
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
        self._timer.stop()
        return True

    @fsm(source=[State.STOPPED, State.ENDED], target="self", exit=lambda self: self._trigger(Events.SESSION_RESET))
    def reset(self) -> bool:
        self.pomodoros = 0
        return True

    def timer_is_up(self) -> bool:
        return not self._timer.is_running()

    @fsm(source=[State.STARTED], target=State.ENDED, condition=timer_is_up)
    @on(Bus, [Events.TIMER_END])
    def _end(self, _, payload: TimerPayload) -> bool:
        previous = self._create_payload(duration=payload.duration)

        if self.current == Type.POMODORO:
            self.pomodoros += 1
            self.current = self._choose_break()
        else:
            self.current = Type.POMODORO

        self.state = State.ENDED
        self._trigger_end(previous)

        return True

    def _trigger_end(self, previous: Payload):
        self._bus.send(
            Events.SESSION_END,
            payload=EndPayload(
                id=uuid.uuid4(),
                duration=self.duration,
                pomodoros=self.pomodoros,
                type=self.current,
                previous=previous,
            ),
        )

    def _choose_break(self):
        return Type.LONG_BREAK if self._is_long_break() else Type.SHORT_BREAK

    def _is_long_break(self) -> bool:
        long_break_interval = self._config.get_int("Timer", "long_break_interval")
        return not self.pomodoros % long_break_interval

    @fsm(source=[State.STOPPED, State.ENDED], target="self", exit=lambda self: self._trigger(Events.SESSION_CHANGE))
    @on(Bus, ["config.timer"])
    def change(self, *_, **kwargs) -> bool:
        self.current = kwargs.get("session", self.current)
        return True

    @property
    def duration(self) -> int:
        minutes = self._config.get_int("Timer", self.current.option)
        return int(minutes * SECONDS_IN_A_MINUTE)

    def _trigger(self, event: Events) -> None:
        self._bus.send(event, payload=self._create_payload())

    def _create_payload(self, **kwargs) -> Payload:
        defaults = {
            "id": uuid.uuid4(),
            "duration": self.duration,
            "pomodoros": self.pomodoros,
            "type": self.current,
        }
        defaults.update(kwargs)
        return Payload(**defaults)
