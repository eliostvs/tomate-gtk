import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Sessions, State
from tomate.pomodoro.session import (
    Session,
    SECONDS_IN_A_MINUTE,
    SessionPayload,
    FinishedSession,
)
from tomate.pomodoro.timer import TimerPayload


@pytest.fixture
def timer_payload(mocker):
    return mocker.Mock(TimerPayload, duration=0)


@pytest.fixture()
def subject(mock_timer, mock_config, mocker):
    from tomate.pomodoro.session import Session
    from tomate.pomodoro.event import Setting

    Setting.receivers.clear()

    return Session(timer=mock_timer, config=mock_config, dispatcher=mocker.Mock())


class TestCountPomodoro:
    def test_count_of_pomodoro(self):
        payload = SessionPayload(
            duration=0,
            state=None,
            task="",
            type=None,
            sessions=[
                FinishedSession(0, Sessions.pomodoro, 0),
                FinishedSession(0, Sessions.pomodoro, 0),
                FinishedSession(0, Sessions.shortbreak, 0),
                FinishedSession(0, Sessions.longbreak, 0),
            ],
        )
        assert len(payload.finished_pomodoros) == 2


class TestSessionStart:
    def test_not_be_able_to_start_when_session_already_started(self, subject):
        subject.state = State.started

        assert not subject.start()

    def test_be_able_to_start_when_session_is_finished(self, subject):
        subject.state = State.finished

        assert subject.start()
        assert subject.state

    def test_be_able_to_start_when_session_is_stopped(self, subject):
        subject.state = State.stopped

        assert subject.start()
        assert subject.state

    def test_trigger_start_event_when_session_start(self, subject):
        subject.start()

        payload = SessionPayload(
            duration=25 * SECONDS_IN_A_MINUTE,
            sessions=[],
            state=State.started,
            task="",
            type=Sessions.pomodoro,
        )

        subject._dispatcher.send.assert_called_once_with(State.started, payload=payload)


class TestSessionStop:
    def test_not_be_able_to_stop_when_session_is_not_started_but_time_it_is(
        self, subject
    ):
        subject._timer.state = State.started
        subject.state = State.stopped

        assert not subject.stop()

    def test_not_be_able_to_stop_when_session_started_but_timer_is_not(self, subject):
        subject._timer.state = State.stopped
        subject.state = State.started

        assert not subject.stop()

    def test_be_able_to_stop_when_session_and_timer_is_running(self, subject):
        subject._timer.state = State.started
        subject.state = State.started

        assert subject.stop()

        assert subject.state == State.stopped

    def test_trigger_stop_event_when_session_stop(self, subject):
        subject.state = State.started
        subject._timer.state = State.started
        subject.stop()

        payload = SessionPayload(
            duration=25 * SECONDS_IN_A_MINUTE,
            sessions=[],
            state=State.stopped,
            task="",
            type=Sessions.pomodoro,
        )

        subject._dispatcher.send.assert_called_with(State.stopped, payload=payload)


class TestSessionReset:
    def test_not_be_able_to_reset_when_session_is_started(self, subject):
        subject.state = State.started

        assert not subject.reset()

    def test_be_able_to_reset_when_session_is_stopped(self, subject):
        subject.state = State.stopped
        subject.sessions = [(Sessions.pomodoro, 25 * SECONDS_IN_A_MINUTE)]

        assert subject.reset()
        assert subject.sessions == []

    def test_be_able_to_reset_whe_session_is_finished(self, subject):
        subject.state = State.finished
        subject.sessions = [(Sessions.pomodoro, 25 * SECONDS_IN_A_MINUTE)]

        assert subject.reset()
        assert subject.sessions == []

    def test_trigger_changed_event_when_session_reset(self, subject):
        subject.state = State.finished
        subject.sessions = [(Sessions.pomodoro, 25 * SECONDS_IN_A_MINUTE)]

        subject.reset()

        payload = SessionPayload(
            duration=25 * SECONDS_IN_A_MINUTE,
            sessions=[],
            state=State.finished,
            task="",
            type=Sessions.pomodoro,
        )

        subject._dispatcher.send.assert_called_with(State.reset, payload=payload)


class TestEndSession:
    def test_not_be_able_to_end_when_state_is_not_valid(self, subject):
        subject.state = State.stopped

        assert not subject.end()

    def test_not_be_able_to_end_when_the_state_is_valid_and_timer_is_running(
        self, subject
    ):
        subject.state = State.started
        subject._timer.state = State.started

        assert not subject.end()

    def test_be_able_to_end_when_state_is_valid_and_timer_is_not_running(
        self, subject, timer_payload
    ):
        subject.state = State.started
        subject._timer.state = State.stopped

        assert subject.end(None, payload=timer_payload)
        assert subject.state == State.finished

    def test_automatically_change_session_to_short_break(self, subject, timer_payload):
        subject._timer.state = State.stopped
        subject.current = Sessions.pomodoro
        subject.state = State.started
        subject.count = 0
        subject._config.get_int.return_value = 4

        subject.end(None, timer_payload)

        assert subject.current == Sessions.shortbreak

    def test_automatically_change_session_to_long_break(self, subject, timer_payload):
        subject.state = State.started
        subject.current = Sessions.pomodoro
        subject.sessions = [
            FinishedSession(id=0, type=Sessions.pomodoro, duration=0)
        ] * 3
        subject._config.get_int.return_value = 4

        assert subject.end(None, payload=timer_payload)
        assert subject.current == Sessions.longbreak

    def test_automatically_change_session_to_pomodoro(self, subject, timer_payload):
        for session_type in (Sessions.longbreak, Sessions.shortbreak):
            subject.current = session_type
            subject._timer.state = State.stopped
            subject.state = State.started

            subject.end(None, timer_payload)

            assert subject.current == Sessions.pomodoro

    def test_trigger_finished_event(self, subject, mocker):
        duration = 25 * SECONDS_IN_A_MINUTE
        subject.state = State.started
        subject._timer.State = State.stopped

        subject.current = Sessions.pomodoro

        subject.end(None, payload=mocker.Mock(duration=duration))

        payload = SessionPayload(
            type=Sessions.shortbreak,
            sessions=[
                FinishedSession(
                    id=mocker.ANY, type=Sessions.pomodoro, duration=duration
                )
            ],
            state=State.finished,
            duration=25 * SECONDS_IN_A_MINUTE,
            task="",
        )

        subject._dispatcher.send.assert_called_with(State.finished, payload=payload)


class TestChangeSessionType:
    def test_not_be_able_to_change_session_type_when_session_already_started(
        self, subject
    ):
        subject.state = State.started

        assert not subject.change(mock_session=None)

    def test_be_able_to_change_session_type_when_session_is_not_started(self, subject):
        for state in (State.stopped, State.finished):
            subject._timer.state = state

            assert subject.change(session=Sessions.shortbreak)
            assert subject.current == Sessions.shortbreak

    def test_trigger_changed_event_when_session_type_change(self, subject):
        subject._config.get_int.return_value = 15
        subject.change(session=Sessions.longbreak)

        payload = SessionPayload(
            type=Sessions.longbreak,
            sessions=[],
            state=State.stopped,
            duration=15 * SECONDS_IN_A_MINUTE,
            task="",
        )

        subject._dispatcher.send.assert_called_with(State.changed, payload=payload)


class TestChangeTask:
    def test_initial_task(self, subject):
        assert subject.task == ""

    def test_change_task_when_session_is_stopped_work(self, subject):
        subject.state = State.stopped
        subject.task = "new task name"

        assert subject.task == "new task name"

    def test_change_task_when_session_is_finished_work(self, subject):
        subject.state = State.finished
        subject.task = "new task name"

        assert subject.task == "new task name"

    def test_change_task_when_session_is_running_not_work(self, subject):
        subject.state = State.started

        subject.task = "new task name"

        assert subject.task == ""


def test_module(graph, mocker, mock_config):
    spec = "tomate.session"
    package = "tomate.pomodoro.session"

    scan_to_graph([package], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]
    assert provider.scope == SingletonScope

    graph.register_instance("tomate.config", mock_config)
    graph.register_factory("tomate.timer", mocker.Mock)
    graph.register_factory("tomate.events.session", mocker.Mock)

    assert isinstance(graph.get(spec), Session)
