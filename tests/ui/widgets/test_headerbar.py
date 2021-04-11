import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events
from tomate.ui.testing import Q, active_shortcut, create_session_end_payload, create_session_payload, refresh_gui
from tomate.ui.widgets import HeaderBar, HeaderBarMenu


class TestHeaderBar:
    @pytest.fixture
    def menu(self, mocker):
        return mocker.Mock(spec=HeaderBarMenu, widget=Gtk.Menu())

    @pytest.fixture
    def headerbar(self, graph, menu, shortcut_engine, session, bus, mocker) -> HeaderBar:
        graph.register_instance("tomate.bus", bus)
        graph.register_instance("tomate.session", session)
        graph.register_factory("tomate.ui.about", mocker.Mock)
        graph.register_factory("tomate.ui.preference", mocker.Mock)
        graph.register_factory("tomate.ui.view", mocker.Mock)
        graph.register_instance("tomate.ui.menu", menu)
        graph.register_instance("tomate.ui.shortcut", shortcut_engine)

        # gtk shortcuts binds leave beyond the scope
        shortcut_engine.disconnect(HeaderBar.START_SHORTCUT)
        shortcut_engine.disconnect(HeaderBar.STOP_SHORTCUT)
        shortcut_engine.disconnect(HeaderBar.RESET_SHORTCUT)

        namespaces = [
            "tomate.pomodoro.proxy",
            "tomate.ui.widgets.headerbar",
        ]

        scan_to_graph(namespaces, graph)

        return graph.get("tomate.ui.headerbar")

    def test_module(self, graph, headerbar):
        instance = graph.get("tomate.ui.headerbar")

        assert isinstance(instance, HeaderBar)
        assert instance is headerbar

    @pytest.mark.parametrize(
        "shortcut,action",
        [
            (HeaderBar.START_SHORTCUT, "start"),
            (HeaderBar.STOP_SHORTCUT, "stop"),
            (HeaderBar.RESET_SHORTCUT, "reset"),
        ],
    )
    def test_shortcuts(self, shortcut, action, headerbar, menu, session, shortcut_engine):
        active_shortcut(shortcut_engine, shortcut)
        getattr(session, action).assert_called_once_with()

    @pytest.mark.parametrize(
        "button_name,tooltip,action",
        [
            (HeaderBar.START_SHORTCUT.name, "Starts the session (Ctrl+S)", "start"),
            (HeaderBar.STOP_SHORTCUT.name, "Stops the session (Ctrl+P)", "stop"),
            (HeaderBar.RESET_SHORTCUT.name, "Clear session count (Ctrl+R)", "reset"),
        ],
    )
    def test_buttons(self, button_name, tooltip, action: str, session, headerbar):
        button = Q.select(headerbar.widget, Q.props("name", button_name))
        assert tooltip == button.props.tooltip_text

        button.emit("clicked")
        refresh_gui()

        getattr(session, action).assert_called_once_with()

    def test_enable_only_the_stop_button_when_session_starts(self, bus, headerbar):
        bus.send(Events.SESSION_START)

        assert Q.select(headerbar.widget, Q.props("name", HeaderBar.START_SHORTCUT.name)).props.visible is False
        assert Q.select(headerbar.widget, Q.props("name", HeaderBar.STOP_SHORTCUT.name)).props.visible is True
        assert Q.select(headerbar.widget, Q.props("name", HeaderBar.RESET_SHORTCUT.name)).props.sensitive is False

    def test_disables_reset_button_when_session_is_reset(self, headerbar, bus, session):
        reset_button = Q.select(headerbar.widget, Q.props("name", headerbar.RESET_SHORTCUT.name))
        reset_button.props.sensitive = True

        bus.send(Events.SESSION_RESET)

        assert reset_button.props.sensitive is False
        assert headerbar.widget.props.title == "No session yet"

    @pytest.mark.parametrize(
        "event,reset,title,payload",
        [
            (Events.SESSION_INTERRUPT, False, "No session yet", create_session_payload()),
            (Events.SESSION_END, True, "Session 1", create_session_end_payload(previous=create_session_payload())),
        ],
    )
    def test_buttons_visibility_and_title_in_the_first_session(self, event, title, reset, headerbar, payload, bus):
        bus.send(event, payload=payload)

        assert Q.select(headerbar.widget, Q.props("name", headerbar.START_SHORTCUT.name)).props.visible is True
        assert Q.select(headerbar.widget, Q.props("name", headerbar.STOP_SHORTCUT.name)).props.visible is False
        assert Q.select(headerbar.widget, Q.props("name", headerbar.RESET_SHORTCUT.name)).props.sensitive is reset
        assert headerbar.widget.props.title == title


class TestHeaderBarMenu:
    @pytest.fixture
    def preference(self, mocker):
        return mocker.Mock(widget=mocker.Mock(spec=Gtk.Dialog))

    @pytest.fixture()
    def about(self, mocker):
        return mocker.Mock(widget=mocker.Mock(spec=Gtk.Dialog))

    @pytest.fixture
    def menu(self, bus, graph, about, preference, window) -> HeaderBarMenu:
        graph.register_instance("tomate.bus", bus)
        graph.register_instance("tomate.ui.about", about)
        graph.register_instance("tomate.ui.preference", preference)
        graph.register_instance("tomate.ui.view", window)

        namespaces = ["tomate.ui.widgets.headerbar", "tomate.pomodoro.proxy"]
        scan_to_graph(namespaces, graph)

        return graph.get("tomate.ui.headerbar.menu")

    def test_module(self, graph, bus, menu):
        instance = graph.get("tomate.ui.headerbar.menu")

        assert isinstance(instance, HeaderBarMenu)
        assert instance is menu

    @pytest.mark.parametrize(
        "widget,label,mock_name",
        [
            ("header.menu.preference", "Preferences", "preference"),
            ("header.menu.about", "About", "about"),
        ],
    )
    def test_menu_items(self, widget, label, mock_name, menu, window, about, preference):
        menu_item = Q.select(menu.widget, Q.props("name", widget))
        assert menu_item.props.label == label

        menu_item.emit("activate")
        refresh_gui()

        dialog = locals()[mock_name].widget
        dialog.run.assert_called_once_with()
        dialog.set_transient_for.assert_called_once_with(window.widget)
