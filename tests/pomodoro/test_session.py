from collections import namedtuple

import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import run_loop_for
from tomate.pomodoro import Sessions, State, SECONDS_IN_A_MINUTE
from tomate.pomodoro.event import Events, connect_events
from tomate.pomodoro.session import Session, Payload as SessionPayload


@pytest.fixture()
def subject(graph, dispatcher, real_config, mocker):
    Events.Config.receivers.clear()
    Events.Timer.receivers.clear()

    mocker.patch("uuid.uuid4", return_value="1234")

    graph.register_instance("tomate.events.timer", Events.Timer)
    graph.register_instance("tomate.events.session", dispatcher)
    graph.register_instance("tomate.config", real_config)
    scan_to_graph(["tomate.pomodoro.timer", "tomate.pomodoro.session"], graph)
    instance = graph.get("tomate.session")

    connect_events(instance)

    return instance


def test_module(graph, subject):
    instance = graph.get("tomate.session")

    assert isinstance(instance, Session)
    assert instance is subject


class TestSessionStart:
    def test_doesnt_start_when_session_already_started(self, subject):
        subject.state = State.started

        assert not subject.start()

    @pytest.mark.parametrize("state", [State.finished, State.stopped])
    def test_starts_when_session_is_not_running(self, state, subject, dispatcher, mocker):
        subject.state = state

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.started, weak=False)

        result = subject.start()

        assert result is True
        payload = SessionPayload(
            id="1234",
            state=State.started,
            type=Sessions.pomodoro,
            pomodoros=0,
            duration=25 * SECONDS_IN_A_MINUTE,
        )
        subscriber.assert_called_once_with(State.started, payload=payload)


class TestSessionStop:
    @pytest.mark.parametrize("state", [State.finished, State.stopped, State.started])
    def test_doesnt_stop_when_session_is_not_running(self, state, subject):
        subject.state = state

        assert not subject.stop()

    def test_stops_when_session_is_running(self, subject, dispatcher, mocker):
        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.stopped, weak=False)

        subject.start()
        result = subject.stop()

        assert result is True
        payload = SessionPayload(
            id="1234",
            type=Sessions.pomodoro,
            state=State.stopped,
            duration=25 * SECONDS_IN_A_MINUTE,
            pomodoros=0,
        )
        subscriber.assert_called_once_with(State.stopped, payload=payload)


class TestSessionReset:
    def test_does_not_reset_when_session_is_running(self, subject):
        subject.state = State.started

        assert not subject.reset()

    @pytest.mark.parametrize(
        "state, session_type, duration",
        [
            (State.finished, Sessions.shortbreak, 5 * SECONDS_IN_A_MINUTE),
            (State.stopped, Sessions.pomodoro, 25 * SECONDS_IN_A_MINUTE),
        ],
    )
    def test_be_able_to_reset_when_session_is_stopped(
        self, state, session_type, duration, subject, dispatcher, mocker
    ):
        subject.state = state
        subject.current = session_type
        subject.pomodoros = 1

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.reset, weak=False)

        result = subject.reset()

        assert result is True
        payload = SessionPayload(
            id="1234",
            state=state,
            type=session_type,
            pomodoros=0,
            duration=duration,
        )
        subscriber.assert_called_once_with(State.reset, payload=payload)


class TestSessionEnd:
    EndScenario = namedtuple(
        "EndScenario", "before_session before_pomodoros after_session after_pomodoros"
    )

    @pytest.mark.parametrize("state", [State.finished, State.stopped])
    def test_doesnt_end_when_session_is_not_running(self, state, subject):
        subject.state = state

        assert not subject.end(None, None)

    def test_doesnt_end_when_session_start_but_time_still_running(self, subject):
        subject.start()

        assert not subject.end(None, None)

    @pytest.mark.parametrize(
        "scenario",
        [
            EndScenario(Sessions.pomodoro, 0, Sessions.shortbreak, 1),
            EndScenario(Sessions.longbreak, 0, Sessions.pomodoro, 0),
            EndScenario(Sessions.shortbreak, 0, Sessions.pomodoro, 0),
            EndScenario(Sessions.pomodoro, 3, Sessions.longbreak, 4),
        ],
    )
    def test_ends_when_session_is_running(
        self, scenario: EndScenario, subject, dispatcher, real_config, mocker
    ):
        subject.current = scenario.before_session
        subject.pomodoros = scenario.before_pomodoros

        real_config.set("Time", "pomodoro_duration", 0.02)
        real_config.set("Timer", "pomodoro_duration", 0.02)
        real_config.set("Timer", "longbreak_duration", 0.02)
        real_config.set("Timer", "shortbreak_duration", 0.02)

        changed = mocker.Mock()
        dispatcher.connect(changed, sender=State.changed, weak=False)

        finished = mocker.Mock()
        dispatcher.connect(finished, sender=State.finished, weak=False)

        subject.start()
        run_loop_for(1)

        finished_payload = SessionPayload(
            id="1234",
            state=State.finished,
            type=scenario.before_session,
            pomodoros=scenario.after_pomodoros,
            duration=0,
        )
        finished.assert_called_once_with(State.finished, payload=finished_payload)

        changed_payload = SessionPayload(
            id="1234",
            state=State.finished,
            type=scenario.after_session,
            pomodoros=scenario.after_pomodoros,
            duration=0,
        )
        changed.assert_called_once_with(State.changed, payload=changed_payload)


class TestSessionChange:
    def test_doesnt_change_when_session_is_running(self, subject):
        subject.state = State.started

        assert not subject.change(session=Sessions.shortbreak)
        assert subject.current is Sessions.pomodoro

    @pytest.mark.parametrize("state", [State.stopped, State.finished])
    def test_changes_when_session_is_not_running(self, state, subject, dispatcher, mocker):
        subject.state = state

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.changed, weak=False)

        Events.Config.send("timer", session=Sessions.longbreak)

        assert subject.current == Sessions.longbreak
        payload = SessionPayload(
            id="1234",
            state=state,
            type=Sessions.longbreak,
            pomodoros=0,
            duration=15 * SECONDS_IN_A_MINUTE,
        )
        subscriber.assert_called_once_with(State.changed, payload=payload)
