import uuid
from collections import namedtuple

from blinker import Signal
from wiring import inject, SingletonScope
from wiring.scanning import register

from . import Sessions, State, SECONDS_IN_A_MINUTE
from .event import Subscriber, on, Events
from .fsm import fsm
from .timer import Payload as TimerPayload, Timer

Payload = namedtuple("SessionPayload", "id state type pomodoros duration")


@register.factory("tomate.session", scope=SingletonScope)
class Session(Subscriber):
    @inject(timer="tomate.timer", config="tomate.config", dispatcher="tomate.events.session")
    def __init__(self, timer: Timer, config, dispatcher: Signal):
        self._config = config
        self._timer = timer
        self._dispatcher = dispatcher
        self.state = State.stopped
        self.current = Sessions.pomodoro
        self.pomodoros = 0

    def is_not_running(self) -> bool:
        return not self.is_running()

    def is_running(self) -> bool:
        return self._timer.state == State.started

    @fsm(
        target=State.started,
        source=[State.stopped, State.finished],
        exit=lambda self: self._trigger(State.started),
    )
    def start(self) -> bool:
        self._timer.start(self.duration)

        return True

    @fsm(
        target=State.stopped,
        source=[State.started],
        condition=is_running,
        exit=lambda self: self._trigger(State.stopped),
    )
    def stop(self) -> bool:
        self._timer.stop()

        return True

    @fsm(
        target="self",
        source=[State.stopped, State.finished],
        exit=lambda self: self._trigger(State.reset),
    )
    def reset(self) -> bool:
        self.pomodoros = 0

        return True

    @fsm(
        target=State.finished,
        source=[State.started],
        condition=is_not_running,
        exit=lambda self: self._trigger(State.changed),
    )
    @on(Events.Timer, [State.finished])
    def end(self, _, payload: TimerPayload) -> bool:
        previous = self.current

        if self._current_session_is(Sessions.pomodoro):
            self.pomodoros += 1
            self.current = self._choose_break()
        else:
            self.current = Sessions.pomodoro

        self._trigger_session_finished(payload.duration, previous)

        return True

    def _trigger_session_finished(self, duration: int, previous: Sessions):
        self._dispatcher.send(
            State.finished,
            payload=self._create_payload(state=State.finished, duration=duration, type=previous),
        )

    def _current_session_is(self, session_type: Sessions) -> bool:
        return self.current == session_type

    def _choose_break(self):
        return Sessions.longbreak if self._is_longbreak() else Sessions.shortbreak

    def _is_longbreak(self) -> bool:
        long_break_interval = self._config.get_int("Timer", "Long Break Interval")
        return not self.pomodoros % long_break_interval

    def _create_payload(self, **kwargs) -> Payload:
        defaults = {
            "id": uuid.uuid4(),
            "duration": self.duration,
            "pomodoros": self.pomodoros,
            "type": self.current,
            "state": self.state,
        }
        defaults.update(kwargs)

        return Payload(**defaults)

    @fsm(
        target="self",
        source=[State.stopped, State.finished],
        exit=lambda self: self._trigger(State.changed),
    )
    @on(Events.Config, ["timer"])
    def change(self, *args, **kwargs) -> bool:
        self.current = kwargs.get("session", self.current)

        return True

    @property
    def duration(self) -> int:
        option = self.current.name + "_duration"
        minutes = self._config.get_int("Timer", option)
        return int(minutes * SECONDS_IN_A_MINUTE)

    def _trigger(self, event: State) -> None:
        self._dispatcher.send(event, payload=self._create_payload())
