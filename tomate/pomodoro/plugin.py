import logging
import os
from typing import List, Optional, Union

import wrapt
from gi.repository import Gtk
from wiring import Graph, SingletonScope, inject
from wiring.scanning import register
from yapsy.ConfigurablePluginManager import ConfigurablePluginManager
from yapsy.IPlugin import IPlugin
from yapsy.PluginInfo import PluginInfo
from yapsy.VersionedPluginManager import VersionedPluginManager

from .config import Config
from .event import Bus, Subscriber

logger = logging.getLogger(__name__)


class Plugin(IPlugin, Subscriber):
    has_settings = False

    def __init__(self):
        super().__init__()
        self.bus = None
        self.graph = None

    def configure(self, bus: Bus, graph: Graph) -> None:
        self.bus = bus
        self.graph = graph

    def activate(self) -> None:
        super().activate()
        self.connect(self.bus)

    def deactivate(self) -> None:
        self.disconnect(self.bus)
        super().deactivate()

    def settings_window(self, parent: Gtk.Widget) -> Union[Gtk.Dialog, None]:
        return None


@register.factory("tomate.plugin", scope=SingletonScope)
class PluginEngine:
    @inject(bus="tomate.bus", config="tomate.config", graph=Graph)
    def __init__(self, bus: Bus, config: Config, graph: Graph):
        self._bus = bus
        self._graph = graph

        logger.debug("action=init paths=%s", config.plugin_paths())
        self._plugin_manager = ConfigurablePluginManager(decorated_manager=VersionedPluginManager())
        self._plugin_manager.setPluginPlaces(config.plugin_paths())
        self._plugin_manager.setPluginInfoExtension("plugin")
        self._plugin_manager.setConfigParser(config.parser, config.save)

    def collect(self) -> None:
        logger.debug("action=collect")
        self._plugin_manager.locatePlugins()
        self._plugin_manager.loadPlugins(callback_after=self._configure_plugin)

    def _configure_plugin(self, plugin: PluginInfo) -> None:
        if plugin.error is None:
            plugin.plugin_object.configure(self._bus, self._graph)

    def deactivate(self, name: str) -> None:
        self._plugin_manager.deactivatePluginByName(name)

    def activate(self, name: str) -> None:
        self._plugin_manager.activatePluginByName(name)

    def all(self) -> List[PluginInfo]:
        logger.debug("action=all")
        return sorted(self._plugin_manager.getAllPlugins(), key=lambda info: info.name)

    def lookup(self, name: str, category="Default") -> Optional[PluginInfo]:
        logger.debug("action=lookup name=%s category=%s", name, category)
        return self._plugin_manager.getPluginByName(name, category)

    def has_plugins(self) -> bool:
        has = len(self.all()) > 0
        logger.debug("action=has_plugin has=%s", has)
        return has

    def remove(self, plugin: object, category="Default") -> None:
        self._plugin_manager.removePluginFromCategory(plugin, category)


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
