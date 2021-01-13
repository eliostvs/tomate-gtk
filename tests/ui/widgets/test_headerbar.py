import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.pomodoro import Sessions, State
from tomate.pomodoro.event import connect_events, Events, Session
from tomate.pomodoro.session import Payload as SessionPayload
from tomate.ui.widgets import HeaderBarMenu, HeaderBar


class TestHeaderBar:
    @pytest.fixture
    def mock_menu(self, mocker):
        return mocker.Mock(HeaderBarMenu, widget=Gtk.Menu())

    @pytest.fixture
    def subject(self, graph, mock_menu, mock_shortcut, mock_session, mocker):
        Session.receivers.clear()

        scan_to_graph(["tomate.ui.widgets.headerbar"], graph)

        graph.register_instance("tomate.ui.menu", mock_menu)
        graph.register_instance("tomate.session", mock_session)
        graph.register_instance("tomate.ui.shortcut", mock_shortcut)
        graph.register_factory("tomate.ui.view", mocker.Mock)
        graph.register_factory("tomate.proxy", mocker.Mock)
        graph.register_factory("tomate.ui.about", mocker.Mock)
        graph.register_factory("tomate.ui.preference", mocker.Mock)

        instance = graph.get("tomate.ui.headerbar")

        connect_events(instance)
        return instance

    def test_module(self, graph, subject):
        instance = graph.get("tomate.ui.headerbar")

        assert isinstance(instance, HeaderBar)
        assert instance is subject

    def test_connect_shortcuts(self, subject, mock_shortcut):
        mock_shortcut.connect.assert_any_call("start", subject._start_session, "<control>s")
        mock_shortcut.connect.assert_any_call("stop", subject._stop_session, "<control>p")
        mock_shortcut.connect.assert_any_call("reset", subject._reset_session, "<control>r")

    def test_start_then_session_when_start_button_is_clicked(
        self, subject, mock_session
    ):
        subject._start_button.emit("clicked")

        refresh_gui()

        mock_session.start.assert_called_once_with()

    def test_stop_the_session_when_stop_button_is_clicked(self, subject, mock_session):
        subject._stop_button.emit("clicked")

        refresh_gui()

        mock_session.stop.assert_called_once_with()

    def test_reset_the_session_when_reset_button_is_clicked(
        self, subject, mock_session
    ):
        subject._reset_button.emit("clicked")

        refresh_gui()

        mock_session.reset.assert_called_once_with()

    def test_enable_only_the_stop_button_when_session_starts(self, subject):
        Session.send(State.started)

        assert subject._stop_button.get_visible() is True
        assert subject._start_button.get_visible() is False
        assert subject._reset_button.get_sensitive() is False

    def test_disables_reset_button_when_session_is_reset(self, subject, mock_session):
        subject._reset_button.set_sensitive(True)
        subject.widget.props.title = "foo"

        Session.send(State.reset)

        assert subject._reset_button.get_sensitive() is False
        assert subject.widget.props.title == "No session yet"

    @pytest.mark.parametrize(
        "state,pomodoros,title",
        [(State.stopped, 0, "No session yet"), (State.finished, 1, "Session 1")],
    )
    def test_buttons_visibility_and_title_in_the_first_session(
        self, state, title, pomodoros, subject, mock_session
    ):
        payload = SessionPayload(
            id="",
            type=Sessions.pomodoro,
            pomodoros=pomodoros,
            state=State.started,
            duration=0,
        )

        Session.send(state, payload=payload)

        assert subject._start_button.get_visible() is True
        assert subject._stop_button.get_visible() is False
        assert subject._reset_button.get_sensitive() is bool(pomodoros)

        assert subject.widget.props.title == title


class TestHeaderBarMenu:
    @pytest.fixture
    def mock_preference(self, mocker):
        return mocker.Mock(widget=mocker.Mock(spec=Gtk.Dialog))

    @pytest.fixture()
    def mock_about(self, mocker):
        return mocker.Mock(widget=mocker.Mock(spec=Gtk.Dialog))

    @pytest.fixture
    def subject(self, mock_proxy, mock_about, mock_preference, mock_view, graph):
        Events.View.receivers.clear()

        graph.register_instance("tomate.ui.view", mock_view)
        graph.register_instance("tomate.proxy", mock_proxy)
        graph.register_instance("tomate.ui.about", mock_about)
        graph.register_instance("tomate.ui.preference", mock_preference)

        scan_to_graph(["tomate.ui.widgets.headerbar"], graph)
        return graph.get("tomate.ui.headerbar.menu")

    def test_module(self, graph, subject):
        instance = graph.get("tomate.ui.headerbar.menu")

        assert isinstance(instance, HeaderBarMenu)
        assert instance is subject

    def test_open_preference_dialog(self, subject, mock_view, mock_preference):
        subject._preference_item.emit("activate")

        refresh_gui()

        mock_preference.widget.run.assert_called_once_with()
        mock_preference.widget.set_transient_for.assert_called_once_with(
            mock_view.widget
        )

    def test_open_about_dialog(self, subject, mock_view, mock_about):
        subject._about_item.emit("activate")

        refresh_gui()

        mock_about.widget.set_transient_for.assert_called_once_with(mock_view.widget)
        mock_about.widget.run.assert_called_once_with()
