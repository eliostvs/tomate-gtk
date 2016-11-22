from __future__ import unicode_literals

import logging
from locale import gettext as _

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import on, View
from wiring import inject, SingletonScope
from wiring.scanning import register

logger = logging.getLogger(__name__)


@register.factory('view.menu', scope=SingletonScope)
class Menu(object):
    @inject(about='view.about', preference='view.preference', lazy_proxy='tomate.proxy')
    def __init__(self, about, preference, lazy_proxy):
        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.view = lazy_proxy('tomate.view')

        self.about_item = Gtk.MenuItem(_('About'))
        self.about_item.connect('activate', self._on_about_item_activate, about)
        self.widget.add(self.about_item)

        self.preference_item = Gtk.MenuItem(_('Preferences'))
        self.preference_item.connect('activate', self._on_preference_item_activate, preference)
        self.widget.add(self.preference_item)

        self.widget.show_all()

    def _on_about_item_activate(self, widget, about):
        about.set_transient_for(self.toplevel)
        about.run()

    def _on_preference_item_activate(self, widget, preference):
        preference.set_transient_for(self.toplevel)
        preference.refresh_plugin()
        preference.run()

    @property
    def toplevel(self):
        return self.view.widget


@register.factory('trayicon.menu', scope=SingletonScope)
class TrayIconMenu(object):
    @inject(view='tomate.view')
    def __init__(self, view):
        self.view = view

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show_item = Gtk.MenuItem(_('Show'), visible=False, no_show_all=True)
        self.show_item.connect('activate', self._on_show_item_activate)
        self.widget.add(self.show_item)

        self.hide_item = Gtk.MenuItem(_('Hide'), visible=True)
        self.hide_item.connect('activate', self._on_hide_item_activate)
        self.widget.add(self.hide_item)

        self.widget.show_all()

    def _on_hide_item_activate(self, widget):
        return self.view.hide()

    def _on_show_item_activate(self, widget):
        return self.view.show()

    @on(View, [State.showed])
    def activate_hide_item(self, sender=None, **kwargs):
        self.hide_item.set_visible(True)
        self.show_item.set_visible(False)

    @on(View, [State.hid])
    def activate_show_item(self, sender=None, **kwargs):
        self.hide_item.set_visible(False)
        self.show_item.set_visible(True)
