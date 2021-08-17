import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events, Session, SessionPayload, SessionType
from tomate.pomodoro.session import State
from tomate.ui.testing import create_session_payload, run_loop_for


@pytest.fixture()
def session(graph, config, bus, mocker):
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.config", config)
    mocker.patch("uuid.uuid4", return_value="1234")
    scan_to_graph(["tomate.pomodoro.timer", "tomate.pomodoro.session"], graph)
    return graph.get("tomate.session")


def test_module(graph, session):
    instance = graph.get("tomate.session")

    assert isinstance(instance, Session)
    assert instance is session


def test_sends_ready_event(bus, mocker, session):
    subscriber = mocker.Mock()
    bus.connect(Events.SESSION_READY, subscriber, weak=False)

    session.ready()

    payload = create_session_payload()
    subscriber.assert_called_once_with(Events.SESSION_READY, payload=payload)


class TestSessionStart:
    def test_not_start_when_session_is_already_running(self, session):
        session.state = State.STARTED

        assert not session.start()

    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_starts_when_session_is_not_running(self, state, session, bus, mocker):
        session.state = state

        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_START, subscriber, weak=False)

        result = session.start()

        assert result is True
        payload = SessionPayload(
            id="1234",
            type=SessionType.POMODORO,
            pomodoros=0,
            duration=25 * 60,
        )
        subscriber.assert_called_once_with(Events.SESSION_START, payload=payload)


class TestSessionStop:
    @pytest.mark.parametrize("state", [State.INITIAL, State.ENDED, State.STOPPED, State.STARTED])
    def test_not_stop_when_session_is_not_running(self, state, session):
        session.state = state

        assert not session.stop()

    def test_stops_when_session_is_running(self, session, bus, mocker):
        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_INTERRUPT, subscriber, False)

        session.ready()
        session.start()
        result = session.stop()

        assert result is True
        payload = SessionPayload(
            id="1234",
            type=SessionType.POMODORO,
            duration=25 * 60,
            pomodoros=0,
        )
        subscriber.assert_called_once_with(Events.SESSION_INTERRUPT, payload=payload)


class TestSessionReset:
    @pytest.mark.parametrize("state", [State.INITIAL, State.STARTED])
    def test_not_reset_when_session_is_running(self, state, session):
        session.state = state

        assert not session.reset()

    @pytest.mark.parametrize(
        "state,session_type,duration",
        [
            (State.ENDED, SessionType.SHORT_BREAK, 5 * 60),
            (State.STOPPED, SessionType.POMODORO, 25 * 60),
        ],
    )
    def test_resets_when_session_is_not_running(self, state, session_type, duration, session, bus, mocker):
        session.state = state
        session.current = session_type
        session.pomodoros = 1

        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_RESET, subscriber, False)

        result = session.reset()

        assert result is True
        payload = SessionPayload(
            id="1234",
            type=session_type,
            pomodoros=0,
            duration=duration,
        )
        subscriber.assert_called_once_with(Events.SESSION_RESET, payload=payload)


class TestSessionEnd:
    @pytest.mark.parametrize("state", [State.INITIAL, State.ENDED, State.STOPPED])
    def test_ends_when_session_is_not_running(self, state, session):
        session.state = state

        assert not session._end(None, None)

    def test_not_end_when_session_start_but_time_still_running(self, session):
        session.start()

        assert not session._end(None, None)

    @pytest.mark.parametrize(
        "old_session,old_pomodoros,new_session,new_pomodoros",
        [
            (SessionType.POMODORO, 0, SessionType.SHORT_BREAK, 1),
            (SessionType.LONG_BREAK, 0, SessionType.POMODORO, 0),
            (SessionType.SHORT_BREAK, 0, SessionType.POMODORO, 0),
            (SessionType.POMODORO, 3, SessionType.LONG_BREAK, 4),
        ],
    )
    def test_ends_when_session_is_running(
        self,
        old_session,
        old_pomodoros,
        new_session,
        new_pomodoros,
        session,
        config,
        bus,
        mocker,
    ):
        session.current = old_session
        session.pomodoros = old_pomodoros

        config.set(config.DURATION_SECTION, "pomodoro_duration", 0.02)
        config.set(config.DURATION_SECTION, "longbreak_duration", 0.02)
        config.set(config.DURATION_SECTION, "shortbreak_duration", 0.02)
        config.parser.getint = config.parser.getfloat

        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_END, subscriber, False)

        session.ready()
        session.start()
        run_loop_for(2)

        payload = create_session_payload(
            type=old_session,
            pomodoros=new_pomodoros,
            duration=1,
        )
        subscriber.assert_called_once_with(Events.SESSION_END, payload=payload)

    def test_changes_session_type(self, bus, config, session, mocker):
        config.set(config.DURATION_SECTION, "pomodoro_duration", 0.02)
        config.parser.getint = config.parser.getfloat

        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_CHANGE, subscriber, False)

        session.ready()
        session.start()
        run_loop_for(2)

        payload = SessionPayload(
            id="1234",
            type=SessionType.SHORT_BREAK,
            duration=5 * 60,
            pomodoros=1,
        )
        subscriber.assert_called_once_with(Events.SESSION_CHANGE, payload=payload)


class TestSessionChange:
    @pytest.mark.parametrize("state", [State.INITIAL, State.STARTED])
    def test_not_change_session(self, state, session):
        session.state = state

        assert session.change(session=SessionType.LONG_BREAK) is False
        assert session.current is SessionType.POMODORO

    @pytest.mark.parametrize(
        "initial,current",
        [
            (State.STOPPED, SessionType.SHORT_BREAK),
            (State.ENDED, SessionType.LONG_BREAK),
        ],
    )
    def test_changes_when_session_is_not_running(self, initial, current, bus, session, config, mocker):
        session.state = initial
        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_CHANGE, subscriber, False)

        assert session.change(session=current) is True
        assert session.current is current

        payload = create_session_payload(
            type=current, duration=config.get_int(config.DURATION_SECTION, current.option) * 60
        )
        subscriber.assert_called_once_with(Events.SESSION_CHANGE, payload=payload)

    @pytest.mark.parametrize("state", [State.STOPPED, State.ENDED])
    def test_changes_when_config_change_and_session_is_not_running(self, session, bus, mocker, state, config):
        session.state = state
        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_CHANGE, subscriber, False)

        config.set(config.DURATION_SECTION, SessionType.POMODORO.option, 20)

        payload = create_session_payload(duration=20 * 60)
        subscriber.assert_called_once_with(Events.SESSION_CHANGE, payload=payload)

    def test_not_change_when_config_changes_and_session_is_running(self, session, bus, config, mocker):
        session.state = State.STARTED
        subscriber = mocker.Mock()
        bus.connect(Events.SESSION_CHANGE, subscriber, False)

        config.set(config.DURATION_SECTION, SessionType.POMODORO.option, 24)

        subscriber.assert_not_called()


@pytest.mark.parametrize(
    "number,session_type",
    [
        (0, SessionType.POMODORO),
        (1, SessionType.SHORT_BREAK),
        (2, SessionType.LONG_BREAK),
    ],
)
def test_type_of(number, session_type):
    assert SessionType.of(number) == session_type


@pytest.mark.parametrize(
    "session_type, option",
    [
        (SessionType.POMODORO, "pomodoro_duration"),
        (SessionType.SHORT_BREAK, "shortbreak_duration"),
        (SessionType.LONG_BREAK, "longbreak_duration"),
    ],
)
def test_type_option(session_type, option):
    assert session_type.option == option
