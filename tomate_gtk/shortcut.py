import logging
from typing import Callable

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.config import Config

logger = logging.getLogger(__name__)


@register.factory("view.shortcut", scope=SingletonScope)
class ShortcutManager(object):
    ACCEL_PATH_TEMPLATE = "<Tomate>/accelerators/{}"
    START = "start"
    STOP = "stop"
    RESET = "reset"
    SHORTCUTS = {START: "<control>s", STOP: "<control>p", RESET: "<control>r"}

    @inject(config="tomate.config")
    def __init__(self, config: Config, accel_group=Gtk.AccelGroup()):
        self.config = config
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
        shortcut = self.config.get(
            self.config.SECTION_SHORTCUTS, name, fallback=self.SHORTCUTS.get(name)
        )

        accel_path = self.ACCEL_PATH_TEMPLATE.format(name)

        key, mod = Gtk.accelerator_parse(shortcut)
        Gtk.AccelMap.add_entry(accel_path, key, mod)

        self.accel_group.connect_by_path(accel_path, fn)

        logger.debug(
            "component=shortcuts action=connect name=%s shortcut=%s", name, shortcut
        )
