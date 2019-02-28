import logging
from collections import namedtuple
from typing import Callable

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.config import Config

logger = logging.getLogger(__name__)

Accelerator = namedtuple("Accelerator", "shortcut key mod path")


@register.factory("view.shortcut", scope=SingletonScope)
class ShortcutManager(object):
    ACCEL_PATH_TEMPLATE = "<tomate>/Global/{}"
    START = "start"
    STOP = "stop"
    RESET = "reset"
    SHORTCUTS = {START: "<control>s", STOP: "<control>p", RESET: "<control>r"}

    @inject(config="tomate.config")
    def __init__(self, config: Config, accel_group=Gtk.AccelGroup()):
        self._config = config
        self.accel_group = accel_group

    def initialize(self, window: Gtk.Window) -> None:
        logger.debug("component=shortcuts action=initialize")

        window.add_accel_group(self.accel_group)

    def change(self, name: str, shortcut: str) -> None:
        logger.debug(
            "component=shortcuts action=configure name=%s shortcut=%s", name, shortcut
        )

        key, mod = Gtk.accelerator_parse(shortcut)
        accel_path = self.ACCEL_PATH_TEMPLATE.format(name)

        Gtk.AccelMap.change_entry(accel_path, key, mod, True)

    def connect(self, name: str, fn: Callable[[], None]) -> None:
        accel = self._get_accelerator(name)

        Gtk.AccelMap.add_entry(accel.path, accel.key, accel.mod)

        self.accel_group.connect_by_path(accel.path, fn)

        logger.debug(
            "component=shortcuts action=connect name=%s shortcut=%s",
            name,
            accel.shortcut,
        )

    def label(self, name: str) -> str:
        accel = self._get_accelerator(name)

        return Gtk.accelerator_get_label(accel.key, accel.mod)

    def _get_accelerator(self, name: str) -> Accelerator:
        shortcut = self._config.get(
            self._config.SECTION_SHORTCUTS, name, fallback=self.SHORTCUTS.get(name)
        )

        key, mod = Gtk.accelerator_parse(shortcut)

        return Accelerator(shortcut, key, mod, self.ACCEL_PATH_TEMPLATE.format(name))
