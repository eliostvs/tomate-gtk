import logging
from collections import namedtuple
from typing import Any, Callable, Tuple

from gi.repository import Gdk, Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

logger = logging.getLogger(__name__)


class Shortcut(namedtuple("Shortcut", ["name", "value"])):
    def __str__(self) -> str:
        return "name={} value={}".format(self.name, self.value)

    @property
    def accel_path(self) -> str:
        return "<tomate>/Global/{}".format(self.name)


@register.factory("tomate.ui.shortcut", scope=SingletonScope)
class ShortcutEngine:
    @inject(config="tomate.config")
    def __init__(self, config, accel_group=Gtk.AccelGroup()):
        self._config = config
        self.accel_group = accel_group

    def init(self, window: Gtk.Window) -> None:
        logger.debug("action=init")
        window.add_accel_group(self.accel_group)

    def change(self, shortcut: Shortcut) -> None:
        logger.debug("action=change %s", shortcut)

        Gtk.AccelMap.change_entry(shortcut.accel_path, *Gtk.accelerator_parse(shortcut.value), True)

    def connect(self, shortcut: Shortcut, callback: Callable[[], Any]) -> None:
        logger.debug("action=connect %s", shortcut)

        Gtk.AccelMap.add_entry(shortcut.accel_path, *self._parse(shortcut))
        self.accel_group.connect_by_path(shortcut.accel_path, callback)

    def disconnect(self, shortcut: Shortcut) -> None:
        logger.debug("action=disconnect %s")

        self.accel_group.disconnect_key(*self._parse(shortcut))

    def label(self, shortcut: Shortcut) -> str:
        return Gtk.accelerator_get_label(*self._parse(shortcut))

    def _parse(self, shortcut: Shortcut) -> Tuple[int, Gdk.ModifierType]:
        accelerator = self._config.get(self._config.SHORTCUT_SECTION, shortcut.name, fallback=shortcut.value)
        return Gtk.accelerator_parse(accelerator)
