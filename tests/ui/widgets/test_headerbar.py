import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui, assert_shortcut_called
from tomate.pomodoro import Sessions, State
from tomate.pomodoro.event import connect_events, Events, Session
from tomate.pomodoro.session import Payload as SessionPayload
from tomate.ui.widgets import HeaderBarMenu, HeaderBar


class TestHeaderBar:
    @pytest.fixture
    def mock_menu(self, mocker):
        return mocker.Mock(HeaderBarMenu, widget=Gtk.Menu())

    @pytest.fixture
    def subject(self, graph, mock_menu, real_shortcut, session, mocker):
        Session.receivers.clear()

        graph.register_instance("tomate.ui.menu", mock_menu)
        graph.register_instance("tomate.session", session)
        graph.register_instance("tomate.ui.shortcut", real_shortcut)
        graph.register_factory("tomate.ui.view", mocker.Mock)
        graph.register_factory("tomate.ui.about", mocker.Mock)
        graph.register_factory("tomate.ui.preference", mocker.Mock)

        real_shortcut.disconnect("button.start", "<control>s")
        real_shortcut.disconnect("button.stop", "<control>p")
        real_shortcut.disconnect("button.reset", "<control>r")

        namespaces = [
            "tomate.pomodoro.proxy",
            "tomate.ui.widgets.headerbar",
        ]

        scan_to_graph(namespaces, graph)

        instance = graph.get("tomate.ui.headerbar")

        connect_events(instance)
        return instance

    def test_module(self, graph, subject):
        instance = graph.get("tomate.ui.headerbar")

        assert isinstance(instance, HeaderBar)
        assert instance is subject

    @pytest.mark.parametrize(
        "shortcut,action",
        [
            ("<control>s", "start"),
            ("<control>p", "stop"),
            ("<control>r", "reset"),
        ],
    )
    def test_shortcuts(self, shortcut, action, mock_menu, real_shortcut, session, subject):
        assert_shortcut_called(real_shortcut, shortcut)
        getattr(session, action).assert_called()

    def test_start_then_session_when_start_button_is_clicked(self, subject, session):
        subject._start_button.emit("clicked")

        refresh_gui()

        session.start.assert_called_once_with()

    def test_stop_the_session_when_stop_button_is_clicked(self, subject, session):
        subject._stop_button.emit("clicked")

        refresh_gui()

        session.stop.assert_called_once_with()

    def test_reset_the_session_when_reset_button_is_clicked(self, subject, session):
        subject._reset_button.emit("clicked")

        refresh_gui()

        session.reset.assert_called_once_with()

    def test_enable_only_the_stop_button_when_session_starts(self, subject):
        Session.send(State.started)

        assert subject._stop_button.get_visible() is True
        assert subject._start_button.get_visible() is False
        assert subject._reset_button.get_sensitive() is False

    def test_disables_reset_button_when_session_is_reset(self, subject, session):
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
        self, state, title, pomodoros, subject, session
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
    def subject(self, mock_about, mock_preference, mock_view, graph):
        Events.View.receivers.clear()

        graph.register_instance("tomate.ui.view", mock_view)
        graph.register_instance("tomate.ui.about", mock_about)
        graph.register_instance("tomate.ui.preference", mock_preference)

        namespaces = ["tomate.ui.widgets.headerbar", "tomate.pomodoro.proxy"]

        scan_to_graph(namespaces, graph)

        return graph.get("tomate.ui.headerbar.menu")

    def test_module(self, graph, subject):
        instance = graph.get("tomate.ui.headerbar.menu")

        assert isinstance(instance, HeaderBarMenu)
        assert instance is subject

    def test_open_preference_dialog(self, subject, mock_view, mock_preference):
        subject._preference_item.emit("activate")

        refresh_gui()

        mock_preference.widget.run.assert_called_once_with()
        mock_preference.widget.set_transient_for.assert_called_once_with(mock_view.widget)

    def test_open_about_dialog(self, subject, mock_view, mock_about):
        subject._about_item.emit("activate")

        refresh_gui()

        mock_about.widget.set_transient_for.assert_called_once_with(mock_view.widget)
        mock_about.widget.run.assert_called_once_with()
