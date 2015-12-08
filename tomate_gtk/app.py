from __future__ import unicode_literals

from tomate.app import Application
from wiring import inject, Module, SingletonScope


class GtkApplication(Application):

    @inject(bus='dbus.session',
            view='tomate.view',
            indicator='tomate.indicator',
            config='tomate.config',
            plugin='tomate.plugin')
    def __init__(self, bus, view, indicator, config, plugin):
        super(GtkApplication, self).__init__(bus, view, config, plugin)
        self.indicator = indicator


class AppModule(Module):
    factories = {
        'tomate.app': (GtkApplication, SingletonScope)
    }
