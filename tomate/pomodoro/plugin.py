import logging
import os

import wrapt
from wiring import SingletonScope, inject
from wiring.scanning import register
from yapsy.ConfigurablePluginManager import ConfigurablePluginManager
from yapsy.IPlugin import IPlugin
from yapsy.PluginManager import PluginManagerSingleton
from yapsy.VersionedPluginManager import VersionedPluginManager

from .event import Subscriber
from .graph import graph

logger = logging.getLogger(__name__)


class StubbySettingsWindow:
    def __init__(self, _):
        pass

    def run(self) -> None:
        pass


class Plugin(IPlugin, Subscriber):
    has_settings = False

    def activate(self):
        super(Plugin, self).activate()
        self.connect(graph.get("tomate.bus"))

    def deactivate(self):
        super(Plugin, self).deactivate()
        self.disconnect(graph.get("tomate.bus"))

    def settings_window(self, parent) -> StubbySettingsWindow:
        return StubbySettingsWindow(parent)


@register.factory("tomate.plugin", scope=SingletonScope)
class PluginManager:
    @inject(config="tomate.config")
    def __init__(self, config):
        logger.debug("action=init paths=%s", config.plugin_paths())

        PluginManagerSingleton.setBehaviour([ConfigurablePluginManager, VersionedPluginManager])
        self._plugin_manager = PluginManagerSingleton.get()
        self._plugin_manager.setPluginPlaces(config.plugin_paths())
        self._plugin_manager.setPluginInfoExtension("plugin")
        self._plugin_manager.setConfigParser(config.parser, config.save)

    def __getattr__(self, attr):
        logger.debug("action=getattr attr=%s", attr)
        try:
            return getattr(self._plugin_manager, attr)
        except KeyError:
            raise AttributeError(attr)


@wrapt.decorator
def suppress_errors(wrapped, _, args, kwargs):
    try:
        return wrapped(*args, **kwargs)
    except Exception as ex:
        if in_debug_mode():
            raise ex

        log = logging.getLogger(__name__)
        log.error(ex, exc_info=True)

    return None


def in_debug_mode():
    return "TOMATE_DEBUG" in os.environ.keys()
