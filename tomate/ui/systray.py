from locale import gettext as _
from typing import Callable, Tuple

from gi.repository import Gio, GLib, Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Events, Subscriber, on


class Systray:
    def show(*args, **kwargs):
        pass

    def hide(*args, **kwargs):
        pass


@register.factory("tomate.ui.systray.menu", scope=SingletonScope)
class Menu(Subscriber):
    @inject(bus="tomate.bus", window="tomate.ui.view")
    def __init__(self, bus: Bus, window):
        self.connect(bus)
        self.widget, self.show_item, self.hide_item = self._create_menu(window)

    def _create_menu(self, window) -> Tuple[Gio.Menu, Gio.MenuItem, Gio.MenuItem]:
        window_widget = getattr(window, "widget", window)
        action_group = Gio.SimpleActionGroup()

        self.show_action = Gio.SimpleAction.new("show", None)
        self.hide_action = Gio.SimpleAction.new("hide", None)
        self.show_action.connect("activate", lambda *_: self._show(window))
        self.hide_action.connect("activate", lambda *_: self._hide(window))
        action_group.add_action(self.show_action)
        action_group.add_action(self.hide_action)

        if hasattr(window_widget, "insert_action_group"):
            window_widget.insert_action_group("systray", action_group)

        menu = Gio.Menu()
        show_item = self._create_menu_item("Show", "systray.show")
        hide_item = self._create_menu_item("Hide", "systray.hide")
        menu.append_item(show_item)
        menu.append_item(hide_item)

        self.hide_action.set_enabled(True)
        self.show_action.set_enabled(False)

        return menu, show_item, hide_item

    def _create_menu_item(self, label: str, action: str) -> Gio.MenuItem:
        menu_item = Gio.MenuItem.new(_(label), action)
        menu_item.set_attribute_value("hidden-when", GLib.Variant("s", "action-disabled"))
        return menu_item

    @staticmethod
    def _show(window) -> None:
        if hasattr(window, "show"):
            window.show()
        elif hasattr(window, "set_visible"):
            window.set_visible(True)

    @staticmethod
    def _hide(window) -> None:
        if hasattr(window, "hide"):
            window.hide()
        elif hasattr(window, "set_visible"):
            window.set_visible(False)

    @on(Events.WINDOW_SHOW)
    def _on_window_show(self, **__):
        self.hide_action.set_enabled(True)
        self.show_action.set_enabled(False)

    @on(Events.WINDOW_HIDE)
    def _on_window_hide(self, **__):
        self.hide_action.set_enabled(False)
        self.show_action.set_enabled(True)
