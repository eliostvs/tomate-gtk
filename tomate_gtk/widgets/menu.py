import logging
from locale import gettext as _

from gi.repository import Gtk
from wiring import inject, SingletonScope
from wiring.scanning import register

from tomate.constant import State
from tomate.event import on, Events

logger = logging.getLogger(__name__)


@register.factory("view.menu", scope=SingletonScope)
class Menu(object):
    @inject(about="view.about", preference="view.preference", lazy_proxy="tomate.proxy")
    def __init__(self, about, preference, lazy_proxy):
        self.view = lazy_proxy("tomate.view")

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.preference_item = Gtk.MenuItem.new_with_label(_("Preferences"))
        self.preference_item.connect("activate", self._on_item_activate, preference)
        self.widget.add(self.preference_item)

        self.about_item = Gtk.MenuItem.new_with_label(_("About"))
        self.about_item.connect("activate", self._on_item_activate, about)
        self.widget.add(self.about_item)

        self.widget.show_all()

    def _on_item_activate(self, _, widget):
        widget.set_transient_for(self.toplevel)
        widget.run()

    @property
    def toplevel(self):
        return self.view.widget


@register.factory("trayicon.menu", scope=SingletonScope)
class TrayIconMenu(object):
    @inject(view="tomate.view")
    def __init__(self, view):
        self.view = view

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show_item = Gtk.MenuItem.new_with_label(_("Show"))
        self.show_item.set_properties(visible=False, no_show_all=True)
        self.show_item.connect("activate", self._on_show_item_activate)
        self.widget.add(self.show_item)

        self.hide_item = Gtk.MenuItem.new_with_label(_("Hide"))
        self.hide_item.set_properties(visible=True)
        self.hide_item.connect("activate", self._on_hide_item_activate)
        self.widget.add(self.hide_item)

        self.widget.show_all()

    def _on_hide_item_activate(self, widget):
        return self.view.hide()

    def _on_show_item_activate(self, widget):
        return self.view.show()

    @on(Events.View, [State.showed])
    def activate_hide_item(self, sender=None, **kwargs):
        self.hide_item.set_visible(True)
        self.show_item.set_visible(False)

    @on(Events.View, [State.hid])
    def activate_show_item(self, sender=None, **kwargs):
        self.hide_item.set_visible(False)
        self.show_item.set_visible(True)
