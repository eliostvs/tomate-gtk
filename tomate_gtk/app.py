from __future__ import unicode_literals

from tomate.app import Application
from wiring import inject, Module, SingletonScope


class GtkApp(Application):

    @inject(bus='dbus.session',
            view='tomate.view',
            indicator='tomate.indicator',
            config='tomate.config',
            plugin='tomate.plugin')
    def __init__(self, bus, view, indicator, config, plugin):
        super(GtkApp, self).__init__(bus, view, config, plugin)

        self.indicator = indicator


class AppProvider(Module):
    factories = {
        'tomate.app': (GtkApp, SingletonScope)
    }
