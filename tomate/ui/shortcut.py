import logging
from collections import namedtuple
from typing import Callable

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

logger = logging.getLogger(__name__)

Metadata = namedtuple("Metadata", "shortcut key mod path")


@register.factory("tomate.ui.shortcut", scope=SingletonScope)
class ShortcutManager:
    ACCEL_PATH_TEMPLATE = "<tomate>/Global/{}"

    @inject(config="tomate.config")
    def __init__(self, config, accel_group=Gtk.AccelGroup()):
        self._config = config
        self.accel_group = accel_group

    def initialize(self, window: Gtk.Window) -> None:
        logger.debug("action=initialize")

        window.add_accel_group(self.accel_group)

    def change(self, name: str, shortcut: str) -> None:
        logger.debug("action=configure name=%s shortcut=%s", name, shortcut)

        key, mod = Gtk.accelerator_parse(shortcut)
        Gtk.AccelMap.change_entry(self._accel_path(name), key, mod, True)

    def connect(self, name: str, callback: Callable[[], bool], fallback: str = None) -> None:
        meta = self._create_metadata(name, fallback)
        Gtk.AccelMap.add_entry(meta.path, meta.key, meta.mod)
        self.accel_group.connect_by_path(meta.path, callback)

        logger.debug("action=connect name=%s shortcut=%s", name, meta.shortcut)

    def label(self, name: str, fallback: str) -> str:
        meta = self._create_metadata(name, fallback)
        return Gtk.accelerator_get_label(meta.key, meta.mod)

    def _create_metadata(self, name: str, fallback: str = None) -> Metadata:
        shortcut = self._config.get(self._config.SECTION_SHORTCUTS, name, fallback=fallback)
        key, mod = Gtk.accelerator_parse(shortcut)
        return Metadata(shortcut, key, mod, self._accel_path(name))

    def _accel_path(self, name: str) -> str:
        return self.ACCEL_PATH_TEMPLATE.format(name)
