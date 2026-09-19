import logging
import os
from typing import Protocol

import wrapt
from yapsy.ConfigurablePluginManager import ConfigurablePluginManager
from yapsy.IPlugin import IPlugin
from yapsy.PluginInfo import PluginInfo
from yapsy.VersionedPluginManager import VersionedPluginManager

from .config import Config
from .event import Bus, Subscriber
from .graph import Injected

logger = logging.getLogger(__name__)


class SettingsWindow(Protocol):
    def run(self) -> object: ...


class Resolve(Protocol):
    """The read-only application-service capability supplied to plugins."""

    def __call__[T](self, key: type[T]) -> T: ...


class Plugin(IPlugin, Subscriber):
    has_settings = False

    def __init__(self):
        super().__init__()
        self.bus: Bus
        self.resolve: Resolve

    def configure(self, bus: Bus, resolve: Resolve) -> None:
        self.bus = bus
        self.resolve = resolve

    def activate(self) -> None:
        super().activate()
        self.connect(self.bus)

    def deactivate(self) -> None:
        self.disconnect(self.bus)
        super().deactivate()

    def settings_window(self, parent) -> SettingsWindow | None:
        return None


class PluginEngine:
    def __init__(self, bus: Injected[Bus], config: Injected[Config], resolve: Injected[Resolve]):
        self._bus = bus

        def resolve_service[T](key: type[T]) -> T:
            return resolve(key)

        self._resolve: Resolve = resolve_service

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
        if plugin.error is None and isinstance(plugin.plugin_object, Plugin):
            plugin.plugin_object.configure(self._bus, self._resolve)

    def deactivate(self, name: str) -> None:
        self._plugin_manager.deactivatePluginByName(name)

    def activate(self, name: str) -> None:
        self._plugin_manager.activatePluginByName(name)

    def all(self) -> list[PluginInfo]:
        logger.debug("action=all")
        return sorted(self._plugin_manager.getAllPlugins(), key=lambda info: info.name)

    def lookup(self, name: str, category="Default") -> PluginInfo | None:
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
    except Exception:
        if in_debug_mode():
            raise

        log = logging.getLogger(__name__)
        log.exception("Failed to execute plugin callback")

    return None


def in_debug_mode():
    return "TOMATE_DEBUG" in os.environ
