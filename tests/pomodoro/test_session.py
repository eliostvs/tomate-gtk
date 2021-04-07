import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import create_session_end_payload, create_session_payload
from tomate.pomodoro.event import Events
from tomate.pomodoro.session import Payload, Session, State, Type
from tomate.ui.testing import run_loop_for


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
    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED, State.STARTED])
    def test_does_not_stop_when_session_is_not_running(self, state, subject):
        subject.state = state

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
        "state,session,duration",
        [
            (State.ENDED, Type.SHORT_BREAK, 5 * 60),
            (State.STOPPED, Type.POMODORO, 25 * 60),
        ],
    )
    def test_resets_when_session_is_not_running(self, state, session, duration, subject, bus, mocker):
        subject.state = state
        subject.current = session
        subject.pomodoros = 1

        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_RESET, weak=False)

        result = subject.reset()

        assert result is True
        payload = Payload(
            id="1234",
            type=session,
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
        "old_session,old_pomodoros,new_session,new_pomodoros",
        [
            (Type.POMODORO, 0, Type.SHORT_BREAK, 1),
            (Type.LONG_BREAK, 0, Type.POMODORO, 0),
            (Type.SHORT_BREAK, 0, Type.POMODORO, 0),
            (Type.POMODORO, 3, Type.LONG_BREAK, 4),
        ],
    )
    def test_ends_when_session_is_running(
        self,
        old_session,
        old_pomodoros,
        new_session,
        new_pomodoros,
        subject,
        config,
        bus,
        mocker,
    ):
        subject.current = old_session
        subject.pomodoros = old_pomodoros

        config.set("Timer", "pomodoro_duration", 0.02)
        config.set("Timer", "longbreak_duration", 0.02)
        config.set("Timer", "shortbreak_duration", 0.02)
        config.parser.getint = config.parser.getfloat

        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_END, weak=False)

        subject.start()
        run_loop_for(2)

        payload = create_session_end_payload(
            type=new_session,
            pomodoros=new_pomodoros,
            duration=1,
            previous=create_session_payload(type=old_session, pomodoros=old_pomodoros, duration=1),
        )
        subscriber.assert_called_once_with(Events.SESSION_END, payload=payload)


class TestSessionChange:
    def test_does_not_change_session_when_it_is_running(self, subject):
        subject.state = State.STARTED

        assert subject.change(session=Type.LONG_BREAK) is False
        assert subject.current is Type.POMODORO

    @pytest.mark.parametrize(
        "state,old,new",
        [
            (State.STOPPED, Type.SHORT_BREAK, Type.SHORT_BREAK),
            (State.ENDED, Type.LONG_BREAK, Type.LONG_BREAK),
        ],
    )
    def test_changes_session_when_it_is_not_running(self, state, old, new, bus, subject, config, mocker):
        subject.state = state
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_CHANGE, weak=False)

        assert subject.change(session=new) is True
        assert subject.current is new
        payload = create_session_payload(type=new, duration=config.get_int("Timer", new.option) * 60)
        subscriber.assert_called_once_with(Events.SESSION_CHANGE, payload=payload)

    @pytest.mark.parametrize("state", [State.STOPPED, State.ENDED])
    def test_listens_config_change_when_session_is_not_running(self, subject, bus, mocker, state, config):
        subject.state = state
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_CHANGE, weak=False)

        config.set("timer", Type.POMODORO.option, 20)

        payload = create_session_payload(duration=20 * 60)
        subscriber.assert_called_once_with(Events.SESSION_CHANGE, payload=payload)

    def test_not_listen_config_change_when_session_is_running(self, subject, bus, config, mocker):
        subject.state = State.STARTED
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.SESSION_CHANGE, weak=False)

        config.set("timer", Type.POMODORO.option, 24)

        subscriber.assert_not_called()


def test_type_of():
    assert Type.POMODORO == Type.of(0)
    assert Type.SHORT_BREAK == Type.of(1)
    assert Type.LONG_BREAK == Type.of(2)


def test_type_option():
    assert Type.POMODORO.option == "pomodoro_duration"
    assert Type.SHORT_BREAK.option == "shortbreak_duration"
    assert Type.LONG_BREAK.option == "longbreak_duration"
