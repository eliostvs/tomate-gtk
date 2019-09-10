import uuid
from collections import namedtuple
from typing import List

from wiring import inject, SingletonScope
from wiring.scanning import register

from . import Sessions, State
from .event import ObservableProperty, Subscriber, on, Events
from .fsm import fsm
from .timer import TimerPayload

SECONDS_IN_A_MINUTE = 60


class SessionPayload(namedtuple("SessionPayload", "type sessions state duration task")):
    __slots__ = ()

    @property
    def finished_pomodoros(self) -> List[Sessions]:
        return Session.finished_pomodoros(self.sessions)


FinishedSession = namedtuple("FinishedSession", "id type duration")


@register.factory("tomate.session", scope=SingletonScope)
class Session(Subscriber):
    @inject(
        timer="tomate.timer", config="tomate.config", dispatcher="tomate.events.session"
    )
    def __init__(self, timer, config, dispatcher):
        self._config = config
        self._timer = timer
        self._dispatcher = dispatcher
        self._task_name = ""
        self.sessions = []
        self.current = Sessions.pomodoro

    def is_running(self) -> bool:
        return self._timer.state == State.started

    def is_not_running(self) -> bool:
        return not self.is_running()

    @fsm(target=State.started, source=[State.stopped, State.finished])
    def start(self) -> bool:
        self._timer.start(self.duration)

        return True

    @fsm(target=State.stopped, source=[State.started], conditions=[is_running])
    def stop(self) -> bool:
        self._timer.stop()

        return True

    @fsm(
        target="self",
        source=[State.stopped, State.finished],
        exit=lambda self: self._trigger(State.reset),
    )
    def reset(self) -> bool:
        self.sessions = []

        return True

    @fsm(target=State.finished, source=[State.started], conditions=[is_not_running])
    @on(Events.Timer, [State.finished])
    def end(self, _, payload: TimerPayload) -> bool:
        self._save_session(payload.duration)

        if self._current_session_is(Sessions.pomodoro):
            self.current = (
                Sessions.longbreak
                if self._is_time_to_long_break
                else Sessions.shortbreak
            )

        else:
            self.current = Sessions.pomodoro

        return True

    @fsm(
        target="self",
        source=[State.stopped, State.finished],
        exit=lambda self: self._trigger(State.changed),
    )
    @on(Events.Setting, ["timer"])
    def change(self, sender=None, **kwargs) -> bool:
        self.current = kwargs.get("session", self.current)

        return True

    @property
    def duration(self) -> int:
        option_name = self.current.name + "_duration"
        seconds = self._config.get_int("Timer", option_name)
        return seconds * SECONDS_IN_A_MINUTE

    @property
    def task(self) -> str:
        return self._task_name

    @task.setter
    def task(self, task_name: str) -> None:
        if self.state in [State.stopped, State.finished]:
            self._task_name = task_name
            self._trigger(State.changed)

    def _current_session_is(self, session_type: Sessions) -> bool:
        return self.current == session_type

    def _trigger(self, event_type: State) -> None:
        payload = SessionPayload(
            duration=self.duration,
            sessions=self.sessions,
            state=self.state,
            task=self.task,
            type=self.current,
        )

        self._dispatcher.send(event_type, payload=payload)

    @property
    def _is_time_to_long_break(self) -> bool:
        long_break_interval = self._config.get_int("Timer", "Long Break Interval")

        return not len(Session.finished_pomodoros(self.sessions)) % long_break_interval

    def _save_session(self, duration: int) -> None:
        finished_session = FinishedSession(
            id=uuid.uuid4(), type=self.current, duration=duration
        )

        self.sessions.append(finished_session)

    @staticmethod
    def finished_pomodoros(sessions: List[Sessions]) -> List[Sessions]:
        return [session for session in sessions if session.type is Sessions.pomodoro]

    state = ObservableProperty(initial=State.stopped, callback=_trigger)
