import logging
from typing import Callable

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.shortcut", scope=SingletonScope)
class ShortcutManager:
    ACCEL_PATH_TEMPLATE = "<tomate>/Global/{}"

    @inject(config="tomate.config")
    def __init__(self, config, accel_group=Gtk.AccelGroup()):
        self._config = config
        self.accel_group = accel_group

    def init(self, window: Gtk.Window) -> None:
        window.add_accel_group(self.accel_group)
        logger.debug("action=init")

    def change(self, name: str, shortcut: str) -> None:
        key, mod = Gtk.accelerator_parse(shortcut)
        Gtk.AccelMap.change_entry(self._accel_path(name), key, mod, True)
        logger.debug("action=configure name=%s shortcut=%s", name, shortcut)

    def connect(self, name: str, callback: Callable[[], bool], fallback: str = None) -> None:
        shortcut = self._shortcut(name, fallback)
        key, mods = Gtk.accelerator_parse(shortcut)
        Gtk.AccelMap.add_entry(self._accel_path(name), key, mods)
        self.accel_group.connect_by_path(self._accel_path(name), callback)
        logger.debug("action=connect name=%s shortcut=%s", name, shortcut)

    def disconnect(self, name: str, fallback: str = None):
        shortcut = self._shortcut(name, fallback)
        key, mods = Gtk.accelerator_parse(shortcut)
        self.accel_group.disconnect_key(key, mods)
        logger.debug("action=disconnect name=%s shortcut=%s", name, shortcut)

    def label(self, name: str, fallback: str = None) -> str:
        key, mods = Gtk.accelerator_parse(self._shortcut(name, fallback))
        return Gtk.accelerator_get_label(key, mods)

    def _accel_path(self, name: str) -> str:
        return self.ACCEL_PATH_TEMPLATE.format(name)

    def _shortcut(self, name: str, fallback: str = None):
        return self._config.get(self._config.SECTION_SHORTCUTS, name, fallback=fallback)
