from _locale import gettext as _

from gi.repository import Gtk
from wiring import Interface, SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import State
from tomate.pomodoro.event import on, Events


class TrayIcon(Interface):
    def show(*args, **kwargs):
        pass

    def hide(*args, **kwargs):
        pass


@register.factory("tomate.ui.tray.menu", scope=SingletonScope)
class Menu:
    @inject(view="tomate.ui.view")
    def __init__(self, view):
        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show_item = Gtk.MenuItem.new_with_label(_("Show"))
        self.show_item.set_properties(visible=False, no_show_all=True)
        self.show_item.connect("activate", lambda _: view.show())
        self.widget.add(self.show_item)

        self.hide_item = Gtk.MenuItem.new_with_label(_("Hide"))
        self.hide_item.set_properties(visible=True)
        self.hide_item.connect("activate", lambda _: view.hide())
        self.widget.add(self.hide_item)

        self.widget.show_all()

    @on(Events.View, [State.showed])
    def _on_view_show(self, *args, **kwargs):
        self.hide_item.set_visible(True)
        self.show_item.set_visible(False)

    @on(Events.View, [State.hid])
    def _on_view_hide(self, *args, **kwargs):
        self.hide_item.set_visible(False)
        self.show_item.set_visible(True)
