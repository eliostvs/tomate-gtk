from __future__ import unicode_literals

from wiring import inject, Module, SingletonScope

from tomate.app import Application


class GtkApplication(Application):

    @inject(bus='dbus.session',
            view='tomate.view',
            indicator='tomate.indicator',
            config='tomate.config',
            plugin='tomate.plugin')
    def __init__(self, bus, view, indicator, config, plugin):
        super(GtkApplication, self).__init__(bus, view, config, plugin)
        self.indicator = indicator


class AppProvider(Module):
    factories = {
        'tomate.app': (GtkApplication, SingletonScope)
    }
