from __future__ import unicode_literals

from locale import gettext as _

from gi.repository import AppIndicator3, Gtk
from tomate.signals import subscribe
from wiring import implements, inject, Interface


class IIndicator(Interface):

    indicator = ''

    def hide():
        pass

    def show():
        pass

    def set_icon(icon):
        pass


class IndicatorMenu(Gtk.Menu):

    @inject(view='tomate.view')
    def __init__(self, view=None):
        Gtk.Menu.__init__(self, halign=Gtk.Align.CENTER)
        self.view = view
        self.show_menu = Gtk.MenuItem(_('Show'), visible=False)
        self.show_menu.connect('activate', self.on_show_menu_activate)
        self.append(self.show_menu)
        self.show_all()

    def on_show_menu_activate(self, widget):
        return self.view.show()


@implements(IIndicator)
class Indicator(object):

    subscriptions = (
        ('session_ended', 'hide'),
        ('window_showed', 'hide'),
        ('window_hid', 'show'),
    )

    @subscribe
    @inject(config='tomate.config', menu='indicator.menu')
    def __init__(self, config=None, menu=None):
        self.config = config

        self.indicator = AppIndicator3.Indicator.new_with_path(
                'tomate',
                'tomate-indicator',
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
                self.config.get_icon_paths()[0]
            )

        self.indicator.set_menu(menu)

    def show(self):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    def hide(self):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    def set_icon(self, icon):
        self.indicator.set_icon(icon)
