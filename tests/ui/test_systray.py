import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events
from tomate.ui import SystrayMenu
from tomate.ui.testing import refresh_gui


@pytest.fixture()
def view():
    return Gtk.Label()


@pytest.fixture
def subject(graph, bus, view):
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.ui.view", view)
    scan_to_graph(["tomate.ui.systray"], graph)
    return graph.get("tomate.ui.systray.menu")


def test_module(graph, subject):
    instance = graph.get("tomate.ui.systray.menu")

    assert isinstance(instance, SystrayMenu)
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
def test_change_items_visibility(event, hide, show, bus, subject):
    bus.send(event)

    assert subject.hide_item.get_visible() is hide
    assert subject.show_item.get_visible() is show
