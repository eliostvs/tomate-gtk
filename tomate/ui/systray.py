from locale import gettext as _
from typing import Tuple, Callable

from gi.repository import Gtk
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

    def _create_menu(self, window) -> Tuple[Gtk.Menu, Gtk.MenuItem, Gtk.MenuItem]:
        menu = Gtk.Menu(halign=Gtk.Align.CENTER)
        menu.add(self._create_menu_item("Show", lambda _: window.show(), visible=False, no_show_all=True))
        menu.add(self._create_menu_item("Hide", lambda _: window.hide(), visible=True))
        menu.show_all()
        return menu, *menu.get_children()

    def _create_menu_item(self, label: str, activate: Callable[[], None], **props) -> Gtk.MenuItem:
        menu_item = Gtk.MenuItem.new_with_label(_(label))
        menu_item.set_properties(**props)
        menu_item.connect("activate", activate)
        return menu_item

    @on(Events.WINDOW_SHOW)
    def _on_window_show(self, *_, **__):
        self.hide_item.props.visible = True
        self.show_item.props.visible = False

    @on(Events.WINDOW_HIDE)
    def _on_window_hide(self, *_, **__):
        self.hide_item.props.visible = False
        self.show_item.props.visible = True
