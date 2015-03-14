from __future__ import unicode_literals

import locale
from locale import gettext as _

from gi.repository import Gtk
from wiring import inject, Module, SingletonScope

locale.textdomain('tomate')


class Appmenu(Gtk.ToolItem):

    @inject(about='view.about',
            preference='view.preference')
    def __init__(self, about, preference):
        self.about = about
        self.preference = preference

        Gtk.ToolItem.__init__(self)

        menu = Gtk.Menu(halign=Gtk.Align.CENTER)

        preferences = Gtk.MenuItem(_('Preferences'))
        preferences.connect('activate', self.on_preferences_menu_activate)
        menu.append(preferences)

        about = Gtk.MenuItem(_('About'))
        about.connect('activate', self.on_about_menu_activate)
        menu.append(about)

        button = Gtk.MenuButton(popup=menu)
        icon = Gtk.Image.new_from_stock('gtk-properties', Gtk.IconSize.LARGE_TOOLBAR)
        button.add(icon)

        self.add(button)

        menu.show_all()

    def on_preferences_menu_activate(self, widget):
        self.preference.refresh_plugin()
        self.preference.run()

    def on_about_menu_activate(self, widget):
        self.about.run()


class AppmenuProvider(Module):
    factories = {
        'view.appmenu': (Appmenu, SingletonScope)
    }
