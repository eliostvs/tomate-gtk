from __future__ import unicode_literals

from locale import gettext as _

import pytest
from conftest import refresh_gui
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State
from tomate.event import Events, connect_events, disconnect_events
from tomate_gtk.widgets.menu import TrayIconMenu, Menu


@pytest.fixture
def preference(mocker):
    return mocker.Mock()


@pytest.fixture()
def about(mocker):
    return mocker.Mock()


@pytest.fixture()
def view(mocker):
    return mocker.Mock(**{'widget.get_visible.return_value': False})


@pytest.fixture()
def proxy(view, mocker):
    mock = mocker.Mock()
    mock.return_value = view

    return mock


@pytest.fixture()
def menu(proxy, about, preference):
    from tomate_gtk.widgets.menu import Menu

    Events.View.receivers.clear()

    return Menu(about, preference, proxy)


@pytest.fixture()
def trayicon_menu(view):
    from tomate_gtk.widgets.menu import TrayIconMenu

    Events.View.receivers.clear()

    return TrayIconMenu(view)


def method_called(result):
    return result[0][0]


class TestMenu(object):
    def test_should_create_preference_item(self, mocker):
        gtk = mocker.patch('tomate_gtk.widgets.menu.Gtk')

        from tomate_gtk.widgets.menu import Menu

        Menu(mocker.Mock(), mocker.Mock(), mocker.Mock)

        gtk.MenuItem.assert_any_call(_('Preferences'))

    def test_should_run_preference_widget_on_preference_item_activate(self, menu, view, preference):
        menu.preference_item.activate()
        refresh_gui()

        preference.set_transient_for.assert_called_once_with(view.widget)
        preference.refresh_plugins.assert_called_once_with()
        preference.run.assert_called_once_with()

    def test_should_create_about_item(self, mocker):
        gtk = mocker.patch('tomate_gtk.widgets.menu.Gtk')

        from tomate_gtk.widgets.menu import Menu

        Menu(mocker.Mock(), mocker.Mock(), mocker.Mock)

        gtk.MenuItem.assert_any_call(_('About'))

    def test_should_run_preference_widget_on_about_item_activate(self, menu, view, about):
        menu.about_item.activate()
        refresh_gui()

        about.set_transient_for.assert_called_once_with(view.widget)
        about.run.assert_called_once_with()


class TestTrayIconMenu(object):
    def test_should_create_show_item(self, mocker):
        gtk = mocker.patch('tomate_gtk.widgets.menu.Gtk')

        from tomate_gtk.widgets.menu import TrayIconMenu

        TrayIconMenu(mocker.Mock())

        gtk.MenuItem.assert_any_call(_('Show'), visible=False, no_show_all=True)

    def test_should_call_plugin_view_when_menu_activate(self, view, trayicon_menu):
        trayicon_menu.show_item.activate()

        refresh_gui()

        view.show.assert_called_once_with()

        assert trayicon_menu.hide_item.get_visible()
        assert not trayicon_menu.show_item.get_visible()

    def test_should_create_hide_item(self, mocker):
        gtk = mocker.patch('tomate_gtk.widgets.menu.Gtk')

        from tomate_gtk.widgets.menu import TrayIconMenu

        TrayIconMenu(mocker.Mock())

        gtk.MenuItem.assert_any_call(_('Hide'), visible=True)

    def test_should_call_view_hide_when_hide_item_activate(self, view, trayicon_menu):
        trayicon_menu.hide_item.activate()
        refresh_gui()

        view.hide.assert_called_once_with()

    def test_should_call_view_show_when_show_item_activate(self, view, trayicon_menu):
        trayicon_menu.show_item.activate()
        refresh_gui()

        view.show.assert_called_once_with()

    def test_hide_item_should_be_true_when_view_is_visible(self, trayicon_menu):
        assert trayicon_menu.hide_item.get_visible()
        assert not trayicon_menu.show_item.get_visible()

    def test_should_call_activate_hide_item_when_view_shows(self, trayicon_menu):
        connect_events(trayicon_menu)

        result = Events.View.send(State.showed)

        assert len(result) == 1
        assert trayicon_menu.activate_hide_item == method_called(result)

    def test_should_call_activate_show_item_view_hides(self, trayicon_menu):
        connect_events(trayicon_menu)

        result = Events.View.send(State.hid)

        assert len(result) == 1
        assert trayicon_menu.activate_show_item == method_called(result)

    def test_should_not_call_menu_after_deactivate(self, trayicon_menu):
        assert len(Events.View.receivers) == 0

        connect_events(trayicon_menu)

        assert len(Events.View.receivers) == 2

        disconnect_events(trayicon_menu)

        result = Events.View.send(State.hid)

        assert len(result) == 0


def test_menu_module(graph, mocker):
    graph.register_instance('view.about', mocker.Mock())
    graph.register_instance('tomate.view', mocker.Mock())
    graph.register_instance('view.preference', mocker.Mock())
    scan_to_graph(['tomate_gtk.widgets.menu'], graph)

    assert 'view.menu' in graph.providers

    provider = graph.providers['view.menu']

    assert provider.scope == SingletonScope

    graph.register_instance('tomate.view', mocker.Mock())
    graph.register_instance('view.preference', mocker.Mock())
    graph.register_instance('tomate.proxy', mocker.Mock())

    assert isinstance(graph.get('view.menu'), Menu)


def test_trayicon_module(graph, mocker):
    scan_to_graph(['tomate_gtk.widgets.menu'], graph)

    assert 'trayicon.menu' in graph.providers

    provider = graph.providers['view.menu']

    assert provider.scope == SingletonScope

    graph.register_instance('tomate.view', mocker.Mock())

    assert isinstance(graph.get('trayicon.menu'), TrayIconMenu)
