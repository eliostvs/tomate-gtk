import pytest
from conftest import refresh_gui
from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Session, connect_events
from tomate.session import Session as ModelSession
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.widgets import HeaderBar

ONE_PAST_SESSION = [("session_type", 0)]

NO_PAST_SESSIONS = []


@pytest.fixture
def model_session(mocker):
    return mocker.Mock(ModelSession)


@pytest.fixture
def header_bar(model_session, mocker):
    Session.receivers.clear()

    subject = HeaderBar(model_session, mocker.Mock(widget=Gtk.Menu()))
    connect_events(subject)

    return subject


def test_header_bar_module(graph, mocker):
    scan_to_graph(["tomate_gtk.widgets.headerbar"], graph)

    assert "view.headerbar" in graph.providers

    graph.register_instance("view.menu", mocker.Mock(widget=Gtk.Menu()))
    graph.register_instance("tomate.session", mocker.Mock())

    provider = graph.providers["view.headerbar"]
    assert provider.scope == SingletonScope

    assert isinstance(graph.get("view.headerbar"), HeaderBar)


class TestSessionStart:
    def test_changes_buttons_visibility_when_session_started_event_is_received(
            self, header_bar
    ):
        Session.send(State.started)

        assert header_bar.start_button.get_visible() is False
        assert header_bar.stop_button.get_visible() is True
        assert header_bar.reset_button.get_sensitive() is False

    def test_starts_session_when_start_button_is_clicked(
            self, header_bar, model_session
    ):
        header_bar.start_button.emit("clicked")

        refresh_gui(0)

        model_session.start.assert_called_once_with()


class TestSessionStopOrFinished:
    def test_buttons_visibility_and_title_with_no_past_sessions(self, header_bar, model_session):
        def side_effect(s):
            if s == NO_PAST_SESSIONS:
                return 0

            raise AssertionError

        model_session.count_pomodoros.side_effect = side_effect

        for state in [State.stopped, State.finished]:
            Session.send(state, sessions=NO_PAST_SESSIONS)

            assert header_bar.start_button.get_visible() is True
            assert header_bar.stop_button.get_visible() is False
            assert header_bar.reset_button.get_sensitive() is False

            assert header_bar.widget.props.title == "No session yet"

    def test_changes_buttons_visibility_and_title_with_one_past_session(self, header_bar, model_session):
        def side_effect(s):
            if s == ONE_PAST_SESSION:
                return 1

            raise AssertionError

        model_session.count_pomodoros.side_effect = side_effect

        for state in [State.stopped, State.finished]:
            Session.send(state, sessions=ONE_PAST_SESSION)

            assert header_bar.start_button.get_visible() is True
            assert header_bar.stop_button.get_visible() is False
            assert header_bar.reset_button.get_sensitive() is True

            assert header_bar.widget.props.title == "Session 1"

    def test_stop_session_when_stop_button_is_clicked(self, header_bar, model_session):
        header_bar.stop_button.emit("clicked")

        refresh_gui(0)

        model_session.stop.assert_called_once_with()


class TestSessionReset:
    def test_disables_reset_button_when_reset_event_is_received(
            self, header_bar, model_session
    ):
        header_bar.reset_button.set_sensitive(True)

        Session.send(State.reset)

        assert header_bar.reset_button.get_sensitive() is False

    def test_reset_session_when_reset_button_is_clicked(
            self, header_bar, model_session
    ):
        header_bar.reset_button.emit("clicked")

        refresh_gui(0)

        model_session.reset.assert_called_once_with()
