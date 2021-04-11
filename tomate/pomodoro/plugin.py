import logging
import os
from typing import List, Optional, Union

import wrapt
from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register
from yapsy.ConfigurablePluginManager import ConfigurablePluginManager
from yapsy.IPlugin import IPlugin
from yapsy.VersionedPluginManager import VersionedPluginManager

from .config import Config
from .event import Subscriber

logger = logging.getLogger(__name__)


class Plugin(IPlugin, Subscriber):
    has_settings = False

    def settings_window(self, parent: Gtk.Widget) -> Union[Gtk.Dialog, None]:
        return None


@register.factory("tomate.plugin", scope=SingletonScope)
class PluginEngine:
    @inject(config="tomate.config")
    def __init__(self, config: Config):
        logger.debug("action=init paths=%s", config.plugin_paths())

        self._plugin_manager = ConfigurablePluginManager(VersionedPluginManager())
        self._plugin_manager.setPluginPlaces(config.plugin_paths())
        self._plugin_manager.setPluginInfoExtension("plugin")
        self._plugin_manager.setConfigParser(config.parser, config.save)

    def collect(self) -> None:
        self._plugin_manager.collectPlugins()

    def deactivate(self, name: str) -> None:
        self._plugin_manager.deactivatePluginByName(name)

    def activate(self, name: str) -> None:
        return self._plugin_manager.activatePluginByName(name)

    def list(self) -> List[object]:
        return sorted(self._plugin_manager.getAllPlugins(), key=lambda p: p.name)

    def get(self, name: str, category="Default") -> Optional[object]:
        return self._plugin_manager.getPluginByName(name, category)

    def has_plugins(self) -> bool:
        return len(self.list()) > 0

    def remove(self, plugin: object, category="Default"):
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
