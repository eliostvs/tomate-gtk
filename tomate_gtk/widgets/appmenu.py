from __future__ import unicode_literals

import locale

from gi.repository import Gtk
from wiring import inject, SingletonScope
from wiring.scanning import register

locale.textdomain('tomate')


@register.factory('view.appmenu', scope=SingletonScope)
class Appmenu(Gtk.ToolItem):
    @inject(menu='view.menu')
    def __init__(self, menu):
        Gtk.ToolItem.__init__(self)

        button = Gtk.MenuButton(popup=menu.widget)
        icon = Gtk.Image.new_from_stock('gtk-properties', Gtk.IconSize.LARGE_TOOLBAR)
        button.add(icon)

        self.add(button)
