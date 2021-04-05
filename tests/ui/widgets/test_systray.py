import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.pomodoro.event import Bus, Events, connect_events
from tomate.ui.widgets import TrayIconMenu


@pytest.fixture()
def view():
    return Gtk.Label()


@pytest.fixture
def subject(graph, view):
    Bus.receivers.clear()

    graph.register_instance("tomate.ui.view", view)
    scan_to_graph(["tomate.ui.widgets.systray"], graph)
    instance = graph.get("tomate.ui.tray.menu")

    connect_events(instance)
    return instance


def test_module(graph, subject):
    instance = graph.get("tomate.ui.tray.menu")

    assert isinstance(instance, TrayIconMenu)
    assert instance is subject


def test_hide_view_when_hide_menu_is_clicked(view, subject):
    view.set_visible(True)

    subject.hide_item.emit("activate")

    refresh_gui()

    assert view.get_visible() is False


def test_show_window_when_hide_item_is_clicked(view, subject):
    view.set_visible(False)

    subject.show_item.emit("activate")

    refresh_gui()

    assert view.get_visible() is True


@pytest.mark.parametrize("event,hide,show", [(Events.WINDOW_HIDE, False, True), (Events.WINDOW_SHOW, True, False)])
def test_change_items_visibility(event, hide, show, subject):
    Bus.send(event)

    assert subject.hide_item.get_visible() is hide
    assert subject.show_item.get_visible() is show
