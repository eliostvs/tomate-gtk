import pytest
from gi.repository import Gtk

from tests.conftest import deliver_events
from tomate.pomodoro import Events
from tomate.ui import SysTray, SystrayMenu
from tomate.ui.testing import refresh_gui


class Tray:
    def show(self) -> None:
        pass

    def hide(self) -> None:
        pass


class EqualTray(Tray):
    def __eq__(self, other: object) -> bool:
        return isinstance(other, EqualTray)


def test_sys_tray_is_unavailable_without_active_systems():
    assert SysTray().available is False


def test_sys_tray_is_available_with_an_active_system():
    registry = SysTray()

    registry.register(Tray())

    assert registry.available is True


def test_sys_tray_registration_is_idempotent_for_the_same_object():
    registry = SysTray()
    tray = Tray()

    registry.register(tray)
    registry.register(tray)
    registry.unregister(tray)

    assert registry.available is False


def test_sys_tray_distinguishes_equal_but_different_objects():
    registry = SysTray()
    first = EqualTray()
    second = EqualTray()

    registry.register(first)
    registry.register(second)
    registry.unregister(first)

    assert registry.available is True


def test_sys_tray_remains_available_until_the_last_system_is_removed():
    registry = SysTray()
    first = Tray()
    second = Tray()

    registry.register(first)
    registry.register(second)
    registry.unregister(first)

    assert registry.available is True

    registry.unregister(second)

    assert registry.available is False


def test_sys_tray_ignores_unknown_system_removal():
    registry = SysTray()
    tray = Tray()

    registry.unregister(tray)

    assert registry.available is False


@pytest.fixture
def window():
    return Gtk.Label()


@pytest.fixture
def systray_menu(bus, window):
    return SystrayMenu(bus, window)


def test_hide_view_when_hide_menu_is_clicked(window, systray_menu):
    window.props.visible = False

    systray_menu.hide_item.emit("activate")

    refresh_gui()

    assert window.props.visible is False


def test_show_window_when_hide_item_is_clicked(window, systray_menu):
    window.props.visible = False

    systray_menu.show_item.emit("activate")

    refresh_gui()

    assert window.props.visible is True


@pytest.mark.parametrize("event,hide,show", [(Events.WINDOW_HIDE, False, True), (Events.WINDOW_SHOW, True, False)])
def test_change_items_visibility(event, hide, show, bus, systray_menu):
    bus.publish(event)
    deliver_events()

    assert systray_menu.hide_item.props.visible is hide
    assert systray_menu.show_item.props.visible is show
