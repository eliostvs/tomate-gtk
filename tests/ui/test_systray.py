import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events
from tomate.ui import SystrayMenu
from tomate.ui.testing import refresh_gui


@pytest.fixture
def window():
    app = Gtk.Application(application_id="com.github.Tomate.Test")
    return Gtk.ApplicationWindow(application=app)


@pytest.fixture
def subject(graph, bus, window):
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.ui.view", window)
    scan_to_graph(["tomate.ui.systray"], graph)
    return graph.get("tomate.ui.systray.menu")


def test_module(graph, subject):
    instance = graph.get("tomate.ui.systray.menu")

    assert isinstance(instance, SystrayMenu)
    assert instance is subject


def test_hide_view_when_hide_menu_is_clicked(window, subject):
    window.set_visible(False)

    subject.hide_action.activate(None)
    refresh_gui()

    assert window.get_visible() is False


def test_show_window_when_hide_item_is_clicked(window, subject):
    window.set_visible(False)

    subject.show_action.activate(None)
    refresh_gui()

    assert window.get_visible() is True


@pytest.mark.parametrize("event,hide,show", [(Events.WINDOW_HIDE, False, True), (Events.WINDOW_SHOW, True, False)])
def test_change_items_visibility(event, hide, show, bus, subject):
    bus.send(event)

    assert subject.hide_action.get_enabled() is hide
    assert subject.show_action.get_enabled() is show
