import pytest
from conftest import refresh_gui
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State
from tomate.event import Events, connect_events
from tomate_gtk.widgets import TrayIconMenu, Menu


@pytest.fixture
def mock_preference(mocker):
    return mocker.Mock()


@pytest.fixture()
def mock_about(mocker):
    return mocker.Mock()


@pytest.fixture()
def mock_view(mocker):
    return mocker.Mock(**{"widget.get_visible.return_value": False})


class TestMenu:
    @staticmethod
    @pytest.fixture
    def subject(lazy_proxy, mock_about, mock_preference, mock_view):
        from tomate_gtk.widgets.menu import Menu

        Events.View.receivers.clear()

        lazy_proxy.side_effect = (
            lambda spec: mock_view if spec == "tomate.view" else None
        )

        return Menu(mock_about, mock_preference, lazy_proxy)

    def test_should_run_preference_widget_on_preference_item_activate(
        self, subject, mock_view, mock_preference
    ):
        subject.preference_item.activate()
        refresh_gui()

        mock_preference.set_transient_for.assert_called_once_with(mock_view.widget)
        mock_preference.run.assert_called_once_with()

    def test_should_run_preference_widget_on_about_item_activate(
        self, subject, mock_view, mock_about
    ):
        subject.about_item.activate()
        refresh_gui()

        mock_about.set_transient_for.assert_called_once_with(mock_view.widget)
        mock_about.run.assert_called_once_with()

    def test_module(self, graph, lazy_proxy, mock_preference, mock_view, mock_about):
        specification = "view.menu"

        graph.register_instance("tomate.view", mock_view)
        graph.register_instance("tomate.proxy", lazy_proxy)
        graph.register_instance("view.about", mock_about)
        graph.register_instance("view.preference", mock_preference)

        scan_to_graph(["tomate_gtk.widgets.menu"], graph)

        assert specification in graph.providers

        provider = graph.providers[specification]

        assert provider.scope == SingletonScope

        assert isinstance(graph.get(specification), Menu)


class TestTrayIconMenu(object):
    @staticmethod
    @pytest.fixture
    def subject(mock_view):
        from tomate_gtk.widgets.menu import TrayIconMenu

        Events.View.receivers.clear()

        instance = TrayIconMenu(mock_view)
        connect_events(instance)

        return instance

    def test_should_show_window_when_show_item_is_clicked(self, mock_view, subject):
        subject.show_item.activate()

        refresh_gui()

        mock_view.show.assert_called_once_with()

    def test_should_change_items_visibility_when_window_is_show(
        self, subject, mock_view
    ):
        Events.View.send(State.showed)

        assert subject.hide_item.get_visible()
        assert not subject.show_item.get_visible()

    def test_should_hide_window_when_hide_item_is_clicked(self, mock_view, subject):
        subject.hide_item.activate()

        refresh_gui()

        mock_view.hide.assert_called_once_with()

    def test_should_change_items_visibility_when_window_is_hide(
        self, subject, mock_view
    ):
        Events.View.send(State.hid)

        assert not subject.hide_item.get_visible()
        assert subject.show_item.get_visible()

    def test_module(self, graph, mock_view):
        specification = "trayicon.menu"

        graph.register_instance("tomate.view", mock_view)

        scan_to_graph(["tomate_gtk.widgets.menu"], graph)

        assert specification in graph.providers

        provider = graph.providers[specification]

        assert provider.scope == SingletonScope

        assert isinstance(graph.get(specification), TrayIconMenu)
