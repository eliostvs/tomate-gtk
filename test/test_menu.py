from __future__ import unicode_literals

import pytest
from mock import Mock
from tomate.constant import State
from tomate.event import Events, connect_events, disconnect_events
from tomate.graph import graph
from wiring import FactoryProvider, Graph, SingletonScope

from tomate_gtk.widgets import MenuModule


@pytest.fixture()
def view(window_is_visible=False):
    Events.View.receivers.clear()

    return Mock(**{'widget.get_visible.return_value': window_is_visible})


@pytest.fixture()
def menu(view):
    graph.providers.clear()

    from tomate_gtk.widgets.menu import Menu

    return Menu(view)


class TestMenu:

    def test_should_call_plugin_view_when_menu_activate(self, view, menu):
        menu._on_show_menu_activate(None)

        view.show.assert_called_once()

        assert menu.hide.get_visible()
        assert not menu.show.get_visible()

    def test_should_call_view_hide_menu_activate(self, view, menu):
        menu._on_hide_menu_activate(None)

        view.hide.assert_called_once()

        assert not menu.hide.get_visible()
        assert menu.show.get_visible()

    def test_hide_menu_should_be_true_when_view_is_visible(self):
        this_view = view(window_is_visible=True)
        this_menu = menu(this_view)

        assert this_view.widget.get_visible()
        assert this_menu.hide.get_visible()
        assert not this_menu.show.get_visible()

    def test_show_menu_should_be_true_when_view_is_not_visible(self, view, menu):

        assert not view.widget.get_visible()
        assert not menu.hide.get_visible()
        assert menu.show.get_visible()


def method_called(result):
    return result[0][0]


@pytest.fixture()
def connect_menu(menu):

    connect_events(menu)

    return menu


class TestIntegrationMenu:

    def test_should_call_menu_active_hide_when_view_is_showing(self, connect_menu):
        result = Events.View.send(State.showing)

        assert len(result) == 1
        assert connect_menu.active_hide_menu == method_called(result)

    def test_should_call_menu_active_show_when_view_is_hding(self, connect_menu):
        result = Events.View.send(State.hiding)

        assert len(result) == 1
        assert connect_menu.active_show_menu == method_called(result)

    def test_should_not_call_menu_after_deactivate(self, menu):
        assert len(Events.View.receivers) == 0

        connect_events(menu)

        assert len(Events.View.receivers) == 2

        disconnect_events(menu)

        result = Events.View.send(State.hiding)

        assert len(result) == 0


def test_menu_module():
    from tomate_gtk.widgets.menu import Menu

    assert MenuModule.providers.keys() == ['view.menu']

    graph = Graph()
    MenuModule().add_to(graph)

    provider = graph.providers['view.menu']

    assert 'view.menu' in graph.providers.keys()

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope

    assert provider.dependencies == {'view': 'tomate.view'}

    graph.register_instance('tomate.view', Mock())

    assert isinstance(graph.get('view.menu'), Menu)
