import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import create_session_end_payload, create_session_payload
from tomate.pomodoro.event import Events
from tomate.pomodoro.session import Payload, Session, State, Type
from tomate.ui.test import run_loop_for


@pytest.fixture()
def subject(graph, config, bus, mocker):
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.config", config)
    mocker.patch("uuid.uuid4", return_value="1234")
    scan_to_graph(["tomate.pomodoro.timer", "tomate.pomodoro.session"], graph)
    return graph.get("tomate.session")


def test_module(graph, subject):
    instance = graph.get("tomate.session")

    assert isinstance(instance, Session)
    assert instance is subject


class TestSessionStart:
    def test_does_not_start_when_session_is_already_running(self, subject):
        subject.state = State.STARTED

        assert not subject.start()

    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_starts_when_session_is_not_running(self, state, subject, bus, mocker):
        subject.state = state

        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_START, weak=False)

        result = subject.start()

        assert result is True
        payload = Payload(
            id="1234",
            type=Type.POMODORO,
            pomodoros=0,
            duration=25 * 60,
        )
        subscriber.assert_called_once_with(Events.SESSION_START, payload=payload)


class TestSessionStop:
    @pytest.mark.parametrize("initial", [State.ENDED, State.STOPPED, State.STARTED])
    def test_does_not_stop_when_session_is_not_running(self, initial, subject):
        subject.state = initial

        assert not subject.stop()

    def test_stops_when_session_is_running(self, subject, bus, mocker):
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_INTERRUPT, weak=False)

        subject.start()
        result = subject.stop()

        assert result is True
        payload = Payload(
            id="1234",
            type=Type.POMODORO,
            duration=25 * 60,
            pomodoros=0,
        )
        subscriber.assert_called_once_with(Events.SESSION_INTERRUPT, payload=payload)


class TestSessionReset:
    def test_does_not_reset_when_session_is_running(self, subject):
        subject.state = State.STARTED

        assert not subject.reset()

    @pytest.mark.parametrize(
        "state,session_type,duration",
        [
            (State.ENDED, Type.SHORT_BREAK, 5 * 60),
            (State.STOPPED, Type.POMODORO, 25 * 60),
        ],
    )
    def test_resets_when_session_is_not_running(self, state, session_type, duration, subject, bus, mocker):
        subject.state = state
        subject.current = session_type
        subject.pomodoros = 1

        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_RESET, weak=False)

        result = subject.reset()

        assert result is True
        payload = Payload(
            id="1234",
            type=session_type,
            pomodoros=0,
            duration=duration,
        )
        subscriber.assert_called_once_with(Events.SESSION_RESET, payload=payload)


class TestSessionEnd:
    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_does_end_when_session_is_not_running(self, state, subject):
        subject.state = state

        assert not subject._end(None, None)

    def test_does_not_end_when_session_start_but_time_still_running(self, subject):
        subject.start()

        assert not subject._end(None, None)

    @pytest.mark.parametrize(
        "initial_session,initial_pomodoros,final_session,final_pomodoros",
        [
            (Type.POMODORO, 0, Type.SHORT_BREAK, 1),
            (Type.LONG_BREAK, 0, Type.POMODORO, 0),
            (Type.SHORT_BREAK, 0, Type.POMODORO, 0),
            (Type.POMODORO, 3, Type.LONG_BREAK, 4),
        ],
    )
    def test_ends_when_session_is_running(
        self,
        initial_session,
        initial_pomodoros,
        final_session,
        final_pomodoros,
        subject,
        config,
        bus,
        mocker,
    ):
        subject.current = initial_session
        subject.pomodoros = initial_pomodoros

        config.set("Timer", "pomodoro_duration", 0.02)
        config.set("Timer", "longbreak_duration", 0.02)
        config.set("Timer", "shortbreak_duration", 0.02)
        config.parser.getint = config.parser.getfloat

        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_END, weak=False)

        subject.start()
        run_loop_for(2)

        payload = create_session_end_payload(
            type=final_session,
            pomodoros=final_pomodoros,
            duration=1,
            previous=create_session_payload(type=initial_session, pomodoros=initial_pomodoros, duration=1),
        )
        subscriber.assert_called_once_with(Events.SESSION_END, payload=payload)


class TestSessionChange:
    @pytest.mark.parametrize(
        "state,session,current,want",
        [
            (State.STARTED, Type.SHORT_BREAK, Type.POMODORO, False),
            (State.STOPPED, Type.SHORT_BREAK, Type.SHORT_BREAK, True),
            (State.ENDED, Type.LONG_BREAK, Type.LONG_BREAK, True),
        ],
    )
    def test_changes_session_based_on_session_state(self, state, session, current, want, subject):
        subject.state = state

        result = subject.change(session=session)

        assert result is want
        assert subject.current is current

    @pytest.mark.parametrize("state", [State.STOPPED, State.ENDED])
    def test_listen_config_changes_when_session_is_not_running(self, subject, bus, mocker, state):
        subject.state = state
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_CHANGE, weak=False)

        bus.send("config.timer")

        payload = Payload(
            id="1234",
            type=Type.POMODORO,
            pomodoros=0,
            duration=25 * 60,
        )
        subscriber.assert_called_once_with(Events.SESSION_CHANGE, payload=payload)

    def test_not_listen_config_changes_when_timer_is_running(self, subject, bus, mocker):
        subject.state = State.STARTED
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_CHANGE, weak=False)

        bus.send("config.timer")

        subscriber.assert_not_called()


def test_type_of():
    assert Type.POMODORO == Type.of(0)
    assert Type.SHORT_BREAK == Type.of(1)
    assert Type.LONG_BREAK == Type.of(2)


def test_type_option():
    assert Type.POMODORO.option == "pomodoro_duration"
    assert Type.SHORT_BREAK.option == "shortbreak_duration"
    assert Type.LONG_BREAK.option == "longbreak_duration"
