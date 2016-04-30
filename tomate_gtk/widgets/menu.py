from __future__ import unicode_literals

import logging
from locale import gettext as _

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Events, on
from wiring import inject, Module, SingletonScope

logger = logging.getLogger(__name__)


class Menu(object):

    @inject(view='tomate.view', about='view.about', preference='view.preference')
    def __init__(self, view, about, preference):
        self.view = view

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show_item = Gtk.MenuItem(_('Show'), visible=False, no_show_all=True)
        self.show_item.connect('activate', self._on_show_item_activate)
        self.widget.add(self.show_item)

        self.hide_item = Gtk.MenuItem(_('Hide'), visible=False, no_show_all=True)
        self.hide_item.connect('activate', self._on_hide_item_activate)
        self.widget.add(self.hide_item)

        self.about_item = Gtk.MenuItem(_('About'))
        self.about_item.connect('activate', self._on_about_item_activate, about)
        self.widget.add(self.about_item)

        self.preference_item = Gtk.MenuItem(_('Preferences'))
        self.preference_item.connect('activate', self._on_preference_item_activate, preference)
        self.widget.add(self.preference_item)

        self._update_menus()

        self.widget.show_all()

    def _update_menus(self):
        if self.view.widget.get_visible():
            self.activate_hide_item()
        else:
            self.activate_show_item()

    def _on_hide_item_activate(self, widget):
        self.activate_show_item()

        return self.view.hide()

    def _on_about_item_activate(self, widget, about):
        about.set_transient_for(self.toplevel)
        about.run()

    def _on_preference_item_activate(self, widget, preference):
        preference.set_transient_for(self.toplevel)
        preference.refresh_plugin()
        preference.run()

    def _on_show_item_activate(self, widget):
        self.activate_hide_item()

        return self.view.show()

    @on(Events.View, [State.showing])
    def activate_hide_item(self, sender=None, **kwargs):
        self.hide_item.set_visible(True)
        self.show_item.set_visible(False)

    @on(Events.View, [State.hiding])
    def activate_show_item(self, sender=None, **kwargs):
        self.hide_item.set_visible(False)
        self.show_item.set_visible(True)

    @property
    def toplevel(self):
        return self.view.widget


class MenuModule(Module):
    factories = {
        'view.menu': (Menu, SingletonScope)
    }
