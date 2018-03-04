import pytest
from conftest import refresh_gui
from gi.repository import Gtk
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State
from tomate.event import Session, connect_events
from tomate_gtk.widgets.appmenu import Appmenu
from tomate_gtk.widgets.toolbar import Toolbar


@pytest.fixture
def tomate_session(mocker):
    return mocker.Mock()


@pytest.fixture
def toolbar(tomate_session) -> Toolbar:
    Session.receivers.clear()

    instance = Toolbar(tomate_session, Gtk.ToolItem())
    connect_events(instance)

    return instance


def test_toolbar_module(graph, mocker):
    scan_to_graph(['tomate_gtk.widgets.toolbar'], graph)

    assert 'view.toolbar' in graph.providers

    graph.register_instance('tomate.menu', Gtk.Menu())
    graph.register_instance('view.menu', mocker.Mock(widget=Gtk.Menu()))
    graph.register_instance('tomate.session', mocker.Mock())
    graph.register_factory('view.appmenu', Appmenu)

    provider = graph.providers['view.toolbar']
    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.toolbar'), Toolbar)


def test_on_sesion_start(toolbar):
    Session.send(State.started)

    assert toolbar.start_button.get_visible() is False
    assert toolbar.stop_button.get_visible() is True
    assert toolbar.reset_button.get_sensitive() is False


def test_on_sesion_stop_in_the_first_session(toolbar):
    Session.send(State.stopped, sessions=0)

    assert toolbar.start_button.get_visible() is True
    assert toolbar.stop_button.get_visible() is False
    assert toolbar.reset_button.get_sensitive() is False


def test_on_sesion_stop_in_the_second_session(toolbar):
    Session.send(State.stopped, sessions=1)

    assert toolbar.start_button.get_visible() is True
    assert toolbar.stop_button.get_visible() is False
    assert toolbar.reset_button.get_sensitive() is True


def test_on_sesion_reset(toolbar):
    toolbar.reset_button.set_sensitive(True)

    Session.send(State.reset)

    assert toolbar.reset_button.get_sensitive() is False


def test_start_session_on_button_click(toolbar, tomate_session):
    toolbar.start_button.emit('clicked')

    refresh_gui(0)

    tomate_session.start.assert_called_once_with()


def test_stop_session_on_button_click(toolbar, tomate_session):
    toolbar.stop_button.emit('clicked')

    refresh_gui(0)

    tomate_session.stop.assert_called_once_with()


def test_reset_session_on_button_click(toolbar, tomate_session):
    toolbar.reset_button.emit('clicked')

    refresh_gui(0)

    tomate_session.reset.assert_called_once_with()
