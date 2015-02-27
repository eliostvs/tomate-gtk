from __future__ import unicode_literals

from locale import gettext as _

from gi.repository import AppIndicator3, Gtk
from wiring import implements, inject, Interface, Module, SingletonScope

from tomate.signals import subscribe


class IIndicator(Interface):

    indicator = ''

    def hide():
        pass

    def show():
        pass

    def set_icon(icon):
        pass


@implements(IIndicator)
class Indicator(object):

    subscriptions = (
        ('session_ended', 'hide'),
        ('window_showed', 'hide'),
        ('window_hid', 'show'),
    )

    @subscribe
    @inject(config='tomate.config', view='tomate.view')
    def __init__(self, config=None, view=None):
        self.config = config

        self.indicator = AppIndicator3.Indicator.new_with_path(
                'tomate',
                'tomate-indicator',
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
                self.config.get_icon_paths()[0]
            )

        menuitem = Gtk.MenuItem(_('Show'), visible=False)
        menuitem.connect('activate', self.on_show_menu_activate)
        menu = Gtk.Menu(halign=Gtk.Align.CENTER)
        menu.add(menuitem)

        self.indicator.set_menu(menu)

    def on_show_menu_activate(self, widget):
        return self.view.show()

    def show(self):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    def hide(self):
        self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

    def set_icon(self, icon):
        self.indicator.set_icon(icon)


class IndicatorProvider(Module):
    factories = {
        'view.indicator': (Indicator, SingletonScope),
    }
