from __future__ import unicode_literals

from wiring import Module, provides, scope, SingletonScope
from yapsy.IPlugin import IPlugin

from .signals import Subscriber


class Plugin(Subscriber, IPlugin):

    def activate(self):
        super(Plugin, self).activate()
        self.connect()

    def deactivate(self):
        super(Plugin, self).deactivate()
        self.disconnect()


class PluginProvider(Module):

    @provides('tomate.plugin')
    @scope(SingletonScope)
    def create_plugin_manager(self):
        from yapsy.ConfigurablePluginManager import ConfigurablePluginManager
        from yapsy.PluginManager import PluginManagerSingleton
        from yapsy.VersionedPluginManager import VersionedPluginManager

        PluginManagerSingleton.setBehaviour([
            ConfigurablePluginManager,
            VersionedPluginManager,
        ])

        return PluginManagerSingleton.get()
