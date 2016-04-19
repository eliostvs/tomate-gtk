from __future__ import unicode_literals

import logging
from locale import gettext as _

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Events, on
from wiring import inject, Module, SingletonScope

logger = logging.getLogger(__name__)


class Menu(object):

    @inject(view='tomate.view')
    def __init__(self, view):
        self.view = view
        self.menu = Gtk.Menu(halign=Gtk.Align.CENTER)

        self.show = Gtk.MenuItem(_('Show'), visible=False, no_show_all=True)
        self.show.connect('activate', self._on_show_menu_activate)
        self.menu.add(self.show)

        self.hide = Gtk.MenuItem(_('Hide'), visible=False, no_show_all=True)
        self.hide.connect('activate', self._on_hide_menu_activate)
        self.menu.add(self.hide)

        self._update_menus()

        self.menu.show_all()

    def _update_menus(self):
        if self.view.widget.get_visible():
            self.active_hide_menu()
        else:
            self.active_show_menu()

    def _on_show_menu_activate(self, widget):
        self.active_hide_menu()

        return self.view.show()

    def _on_hide_menu_activate(self, widget):
        self.active_show_menu()

        return self.view.hide()

    @on(Events.View, [State.showing])
    def active_hide_menu(self, sender=None, **kwargs):
        self.hide.set_visible(True)
        self.show.set_visible(False)

    @on(Events.View, [State.hiding])
    def active_show_menu(self, sender=None, **kwargs):
        self.hide.set_visible(False)
        self.show.set_visible(True)

    @property
    def widget(self):
        return self.menu


class MenuModule(Module):
    factories = {
        'view.menu': (Menu, SingletonScope)
    }
