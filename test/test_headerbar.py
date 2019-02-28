import pytest
from conftest import refresh_gui
from gi.repository import Gtk
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State, Sessions
from tomate.event import Session, connect_events
from tomate.session import SessionPayload, FinishedSession
from tomate_gtk.shortcut import ShortcutManager
from tomate_gtk.widgets.headerbar import HeaderBar
from tomate_gtk.widgets.menu import Menu

ONE_FINISHED_SESSION = [FinishedSession(1, Sessions.pomodoro, 10)]

NO_FINISHED_SESSIONS = []


@pytest.fixture
def mock_menu(mocker):
    return mocker.Mock(Menu, widget=Gtk.Menu())


@pytest.fixture
def mock_shortcuts(mocker):
    instance = mocker.Mock(
        ShortcutManager,
        START=ShortcutManager.START,
        STOP=ShortcutManager.STOP,
        RESET=ShortcutManager.RESET,
    )

    instance.label.side_effect = lambda name: name

    return instance


@pytest.fixture
def subject(session, mock_menu, mock_shortcuts):
    Session.receivers.clear()

    subject = HeaderBar(session, mock_menu, mock_shortcuts)

    connect_events(subject)

    return subject


def test_module(graph, session, mock_menu, mock_shortcuts):
    spec = "view.headerbar"

    scan_to_graph(["tomate_gtk.widgets.headerbar"], graph)

    assert spec in graph.providers

    graph.register_instance("view.menu", mock_menu)
    graph.register_instance("tomate.session", mock_shortcuts)
    graph.register_instance("view.shortcut", mock_shortcuts)

    provider = graph.providers[spec]
    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), HeaderBar)


def test_connect_shortcuts(mock_shortcuts, subject):
    mock_shortcuts.connect.assert_any_call(
        ShortcutManager.START, subject.on_start_button_clicked
    )
    assert subject.start_button.get_tooltip_text() == "Starts the session (start)"

    mock_shortcuts.connect.assert_any_call(
        ShortcutManager.STOP, subject.on_stop_button_clicked
    )
    assert subject.stop_button.get_tooltip_text() == "Stops the session (stop)"

    mock_shortcuts.connect.assert_any_call(
        ShortcutManager.RESET, subject.on_reset_button_clicked
    )
    assert subject.reset_button.get_tooltip_text() == "Clear the count of sessions (reset)"


class TestSessionStart:
    def test_changes_buttons_visibility_when_session_started_event_is_received(
        self, subject
    ):
        Session.send(State.started)

        assert subject.start_button.get_visible() is False
        assert subject.stop_button.get_visible() is True
        assert subject.reset_button.get_sensitive() is False

    def test_starts_session_when_start_button_is_clicked(self, subject, session):
        subject.start_button.emit("clicked")

        refresh_gui(0)

        session.start.assert_called_once_with()


class TestSessionStopOrFinished:
    def test_buttons_visibility_and_title_with_no_past_sessions(self, subject, session):

        payload = SessionPayload(
            type=Sessions.pomodoro,
            sessions=NO_FINISHED_SESSIONS,
            state=State.started,
            duration=0,
            task="",
        )

        for state in [State.stopped, State.finished]:
            Session.send(state, payload=payload)

            assert subject.start_button.get_visible() is True
            assert subject.stop_button.get_visible() is False
            assert subject.reset_button.get_sensitive() is False

            assert subject.widget.props.title == "No session yet"

    def test_changes_buttons_visibility_and_title_with_one_past_session(
        self, subject, session
    ):

        payload = SessionPayload(
            type=Sessions.pomodoro,
            sessions=ONE_FINISHED_SESSION,
            state=State.finished,
            duration=1,
            task="",
        )

        for state in [State.stopped, State.finished]:
            Session.send(state, payload=payload)

            assert subject.start_button.get_visible() is True
            assert subject.stop_button.get_visible() is False
            assert subject.reset_button.get_sensitive() is True

            assert subject.widget.props.title == "Session 1"

    def test_stop_session_when_stop_button_is_clicked(self, subject, session):
        subject.stop_button.emit("clicked")

        refresh_gui(0)

        session.stop.assert_called_once_with()


class TestSessionReset:
    def test_disables_reset_button_when_reset_event_is_received(self, subject, session):
        subject.reset_button.set_sensitive(True)

        Session.send(State.reset)

        assert subject.reset_button.get_sensitive() is False

    def test_reset_session_when_reset_button_is_clicked(self, subject, session):
        subject.reset_button.emit("clicked")

        refresh_gui(0)

        session.reset.assert_called_once_with()
