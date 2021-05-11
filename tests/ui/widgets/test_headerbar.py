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
        graph.register_instance("tomate.ui.menu", menu)
        graph.register_instance("tomate.ui.shortcut", shortcut_engine)

        # gtk shortcuts binds leave beyond the scope
        shortcut_engine.disconnect(HeaderBar.START_SHORTCUT)
        shortcut_engine.disconnect(HeaderBar.STOP_SHORTCUT)
        shortcut_engine.disconnect(HeaderBar.RESET_SHORTCUT)

        namespaces = ["tomate.ui.widgets.headerbar"]

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
        assert active_shortcut(shortcut_engine, shortcut)

        getattr(session, action).assert_called_once_with()

    @pytest.mark.parametrize(
        "button_name,action",
        [
            (HeaderBar.START_SHORTCUT.name, "start"),
            (HeaderBar.STOP_SHORTCUT.name, "stop"),
            (HeaderBar.RESET_SHORTCUT.name, "reset"),
        ],
    )
    def test_change_session(self, button_name, action, session, headerbar):
        button = Q.select(headerbar.widget, Q.props("name", button_name))

        button.emit("clicked")
        refresh_gui()

        getattr(session, action).assert_called_once_with()

    @pytest.mark.parametrize(
        "button_name,tooltip",
        [
            (HeaderBar.START_SHORTCUT.name, "Starts the session (Ctrl+S)"),
            (HeaderBar.STOP_SHORTCUT.name, "Stops the session (Ctrl+P)"),
            (HeaderBar.RESET_SHORTCUT.name, "Clear session count (Ctrl+R)"),
            (HeaderBarMenu.PREFERENCE_SHORTCUT.name, "Open preferences (Ctrl+,)"),
        ],
    )
    def test_buttons_tooltip(self, button_name, tooltip, headerbar):
        button = Q.select(headerbar.widget, Q.props("name", button_name))
        assert tooltip == button.props.tooltip_text

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
    def menu(self, bus, about, preference, shortcut_engine) -> HeaderBarMenu:
        shortcut_engine.disconnect(HeaderBarMenu.PREFERENCE_SHORTCUT)

        return HeaderBarMenu(bus, about, preference, shortcut_engine)

    def test_module(self, about, bus, preference, graph, shortcut_engine):
        graph.register_instance("tomate.bus", bus)
        graph.register_instance("tomate.ui.about", about)
        graph.register_instance("tomate.ui.preference", preference)
        graph.register_instance("tomate.ui.shortcut", shortcut_engine)

        namespaces = ["tomate.ui.widgets.headerbar"]
        scan_to_graph(namespaces, graph)

        instance = graph.get("tomate.ui.headerbar.menu")

        assert isinstance(instance, HeaderBarMenu)
        assert instance is graph.get("tomate.ui.headerbar.menu")

    @pytest.mark.parametrize(
        "widget,label,mock_name",
        [
            ("header.menu.preference", "Preferences", "preference"),
            ("header.menu.about", "About", "about"),
        ],
    )
    def test_menu_items(self, widget, label, mock_name, menu, about, preference):
        menu_item = Q.select(menu.widget, Q.props("name", widget))
        assert menu_item.props.label == label

        menu_item.emit("activate")
        refresh_gui()

        dialog = locals()[mock_name].widget
        dialog.run.assert_called_once_with()

    def test_shortcut(self, menu, shortcut_engine, preference):
        assert active_shortcut(shortcut_engine, HeaderBarMenu.PREFERENCE_SHORTCUT) is True

        preference.widget.run.assert_called_once_with()
