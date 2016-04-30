from __future__ import unicode_literals

from locale import gettext as _

import pytest
from mock import Mock, patch
from tomate.constant import State
from tomate.event import Events, connect_events, disconnect_events
from wiring import FactoryProvider, Graph, SingletonScope

from tomate_gtk.widgets import MenuModule
from util import refresh_gui


@pytest.fixture
def preference():
    return Mock()


@pytest.fixture()
def about():
    return Mock()


@pytest.fixture()
def view():
    return Mock(**{'widget.get_visible.return_value': False})


@pytest.fixture()
def proxy(view):
    mock = Mock()
    mock.return_value = view

    return mock


@pytest.fixture()
def menu(proxy, about, preference):
    from tomate_gtk.widgets.menu import Menu

    Events.View.receivers.clear()

    return Menu(about, preference, proxy)


def method_called(result):
    return result[0][0]


@patch('tomate_gtk.widgets.menu.Gtk')
def test_should_create_show_item(Gtk):
    from tomate_gtk.widgets.menu import Menu

    Menu(Mock(), Mock(), Mock())

    Gtk.MenuItem.assert_any_call(_('Show'), visible=False, no_show_all=True)


def test_should_call_plugin_view_when_menu_activate(view, menu):
    menu.show_item.activate()
    refresh_gui()

    view.show.assert_called_once()

    assert menu.hide_item.get_visible()
    assert not menu.show_item.get_visible()


@patch('tomate_gtk.widgets.menu.Gtk')
def test_should_create_hide_item(Gtk):
    from tomate_gtk.widgets.menu import Menu

    Menu(Mock(), Mock(), Mock())

    Gtk.MenuItem.assert_any_call(_('Hide'), visible=True)


def test_should_call_view_hide_item_activate(view, menu):
    menu.hide_item.activate()
    refresh_gui()

    view.hide.assert_called_once()

    assert not menu.hide_item.get_visible()
    assert menu.show_item.get_visible()


def test_hide_item_should_be_true_when_view_is_visible(menu):
    assert menu.hide_item.get_visible()
    assert not menu.show_item.get_visible()


def test_should_call_activate_hide_item_when_view_shows(menu):
    connect_events(menu)

    result = Events.View.send(State.showing)

    assert len(result) == 1
    assert menu.activate_hide_item == method_called(result)


def test_should_call_activate_show_item_view_hides(menu):
    connect_events(menu)

    result = Events.View.send(State.hiding)

    assert len(result) == 1
    assert menu.activate_show_item == method_called(result)


def test_should_not_call_menu_after_deactivate(menu):
    assert len(Events.View.receivers) == 0

    connect_events(menu)

    assert len(Events.View.receivers) == 2

    disconnect_events(menu)

    result = Events.View.send(State.hiding)

    assert len(result) == 0


@patch('tomate_gtk.widgets.menu.Gtk')
def test_should_create_about_item(Gtk):
    from tomate_gtk.widgets.menu import Menu

    Menu(Mock(), Mock(), Mock)

    Gtk.MenuItem.assert_any_call(_('About'))


def test_should_run_about_widget_on_about_item_activate(menu, view, about):
    menu.about_item.activate()

    refresh_gui()

    about.run.assert_called_once_with()
    about.set_transient_for.assert_called_once_with(view.widget)


@patch('tomate_gtk.widgets.menu.Gtk')
def test_should_create_preference_item(Gtk):
    from tomate_gtk.widgets.menu import Menu

    Menu(Mock(), Mock(), Mock)

    Gtk.MenuItem.assert_any_call(_('Preferences'))


def test_should_run_preference_widget_on_preference_item_activate(menu, view, preference):
    menu.preference_item.activate()
    refresh_gui()

    preference.set_transient_for.assert_called_once_with(view.widget)
    preference.refresh_plugin.assert_called_once_winth()
    preference.run.assert_called_once_with()


def test_menu_module():
    from tomate_gtk.widgets.menu import Menu

    assert MenuModule.providers.keys() == ['view.menu']

    graph = Graph()
    MenuModule().add_to(graph)

    provider = graph.providers['view.menu']

    assert 'view.menu' in graph.providers.keys()

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope

    assert provider.dependencies == {'proxy': 'tomate.proxy',
                                     'about': 'view.about',
                                     'preference': 'view.preference'}

    graph.register_instance('view.about', Mock())
    graph.register_instance('view.preference', Mock())
    graph.register_instance('tomate.proxy', Mock())

    assert isinstance(graph.get('view.menu'), Menu)
