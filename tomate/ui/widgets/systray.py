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
class Menu(object):
    @inject(view="tomate.ui.view")
    def __init__(self, view):
        self._view = view

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self._show_item = Gtk.MenuItem.new_with_label(_("Show"))
        self._show_item.set_properties(visible=False, no_show_all=True)
        self._show_item.connect("activate", self._show_window)
        self.widget.add(self._show_item)

        self._hide_item = Gtk.MenuItem.new_with_label(_("Hide"))
        self._hide_item.set_properties(visible=True)
        self._hide_item.connect("activate", self._hide_window)
        self.widget.add(self._hide_item)

        self.widget.show_all()

    def _hide_window(self, _):
        return self._view.hide()

    def _show_window(self, _):
        return self._view.show()

    @on(Events.View, [State.showed])
    def _on_view_show(self, *args, **kwargs):
        self._hide_item.set_visible(True)
        self._show_item.set_visible(False)

    @on(Events.View, [State.hid])
    def _on_view_hide(self, *args, **kwargs):
        self._hide_item.set_visible(False)
        self._show_item.set_visible(True)
