import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import assert_shortcut_called, create_session_end_payload, create_session_payload, refresh_gui
from tomate.pomodoro.event import Bus, Events, connect_events
from tomate.ui.widgets import HeaderBar, HeaderBarMenu


class TestHeaderBar:
    @pytest.fixture
    def menu(self, mocker):
        return mocker.Mock(HeaderBarMenu, widget=Gtk.Menu())

    @pytest.fixture
    def subject(self, graph, menu, shortcut_manager, session, mocker):
        Bus.receivers.clear()

        graph.register_instance("tomate.ui.menu", menu)
        graph.register_instance("tomate.session", session)
        graph.register_instance("tomate.ui.shortcut", shortcut_manager)
        graph.register_factory("tomate.ui.view", mocker.Mock)
        graph.register_factory("tomate.ui.about", mocker.Mock)
        graph.register_factory("tomate.ui.preference", mocker.Mock)

        shortcut_manager.disconnect("button.start", "<control>s")
        shortcut_manager.disconnect("button.stop", "<control>p")
        shortcut_manager.disconnect("button.reset", "<control>r")

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
    def test_shortcuts(self, shortcut, action, menu, shortcut_manager, session, subject):
        assert_shortcut_called(shortcut_manager, shortcut)
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
        Bus.send(Events.SESSION_START)

        assert subject._stop_button.get_visible() is True
        assert subject._start_button.get_visible() is False
        assert subject._reset_button.get_sensitive() is False

    def test_disables_reset_button_when_session_is_reset(self, subject, session):
        subject._reset_button.set_sensitive(True)

        Bus.send(Events.SESSION_RESET)

        assert subject._reset_button.get_sensitive() is False
        assert subject.widget.props.title == "No session yet"

    @pytest.mark.parametrize(
        "event,pomodoros,title,payload",
        [
            (Events.SESSION_INTERRUPT, 0, "No session yet", create_session_payload()),
            (Events.SESSION_END, 1, "Session 1", create_session_end_payload(previous=create_session_payload())),
        ],
    )
    def test_buttons_visibility_and_title_in_the_first_session(
        self, event, title, pomodoros, subject, session, payload
    ):
        Bus.send(event, payload=payload)

        assert subject._start_button.get_visible() is True
        assert subject._stop_button.get_visible() is False
        assert subject._reset_button.get_sensitive() is bool(pomodoros)

        assert subject.widget.props.title == title


class TestHeaderBarMenu:
    @pytest.fixture
    def preference(self, mocker):
        return mocker.Mock(widget=mocker.Mock(spec=Gtk.Dialog))

    @pytest.fixture()
    def about(self, mocker):
        return mocker.Mock(widget=mocker.Mock(spec=Gtk.Dialog))

    @pytest.fixture
    def subject(self, about, preference, view, graph):
        Bus.receivers.clear()

        graph.register_instance("tomate.ui.view", view)
        graph.register_instance("tomate.ui.about", about)
        graph.register_instance("tomate.ui.preference", preference)

        namespaces = ["tomate.ui.widgets.headerbar", "tomate.pomodoro.proxy"]

        scan_to_graph(namespaces, graph)

        return graph.get("tomate.ui.headerbar.menu")

    def test_module(self, graph, subject):
        instance = graph.get("tomate.ui.headerbar.menu")

        assert isinstance(instance, HeaderBarMenu)
        assert instance is subject

    def test_open_preference_dialog(self, subject, view, preference):
        subject._preference_item.emit("activate")

        refresh_gui()

        preference.widget.run.assert_called_once_with()
        preference.widget.set_transient_for.assert_called_once_with(view.widget)

    def test_open_about_dialog(self, subject, view, about):
        subject._about_item.emit("activate")

        refresh_gui()

        about.widget.set_transient_for.assert_called_once_with(view.widget)
        about.widget.run.assert_called_once_with()
