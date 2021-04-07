from _locale import gettext as _

from gi.repository import Gtk
from wiring import Interface, SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro.event import Events, Subscriber, on


class Systray(Interface):
    def show(*args, **kwargs):
        pass

    def hide(*args, **kwargs):
        pass


@register.factory("tomate.ui.systray.menu", scope=SingletonScope)
class Menu(Subscriber):
    @inject(bus="tomate.bus", window="tomate.ui.view")
    def __init__(self, bus, window):
        self.connect(bus)
        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show_item = Gtk.MenuItem.new_with_label(_("Show"))
        self.show_item.set_properties(visible=False, no_show_all=True)
        self.show_item.connect("activate", lambda _: window.show())
        self.widget.add(self.show_item)

        self.hide_item = Gtk.MenuItem.new_with_label(_("Hide"))
        self.hide_item.set_properties(visible=True)
        self.hide_item.connect("activate", lambda _: window.hide())
        self.widget.add(self.hide_item)

        self.widget.show_all()

    @on(Events.WINDOW_SHOW)
    def _on_window_show(self, *_, **__):
        self.hide_item.set_visible(True)
        self.show_item.set_visible(False)

    @on(Events.WINDOW_HIDE)
    def _on_window_hide(self, *_, **__):
        self.hide_item.set_visible(False)
        self.show_item.set_visible(True)