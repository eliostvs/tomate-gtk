import logging
from collections import namedtuple
from typing import Dict, Tuple

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
    def __init__(self, config):
        self._config = config
        self._controller = Gtk.ShortcutController()
        self._shortcuts: Dict[str, Gtk.Shortcut] = {}
        self._actions: Dict[str, str] = {}

    def init(self, window: Gtk.Window) -> None:
        logger.debug("action=init")
        window.add_controller(self._controller)

    def change(self, shortcut: Shortcut) -> None:
        logger.debug("action=change %s", shortcut)
        action_name = self._actions.get(shortcut.name)
        self.disconnect(shortcut)
        if action_name:
            self.connect(shortcut, action_name)

    def connect(self, shortcut: Shortcut, action_name: str) -> None:
        logger.debug("action=connect %s", shortcut)
        trigger = Gtk.ShortcutTrigger.parse_string(self._accel_str(shortcut))
        action = Gtk.NamedAction.new(action_name)
        gtk_shortcut = Gtk.Shortcut.new(trigger, action)
        self._controller.add_shortcut(gtk_shortcut)
        self._shortcuts[shortcut.name] = gtk_shortcut
        self._actions[shortcut.name] = action_name

    def disconnect(self, shortcut: Shortcut) -> None:
        logger.debug("action=disconnect %s")
        gtk_shortcut = self._shortcuts.pop(shortcut.name, None)
        if gtk_shortcut is not None:
            self._controller.remove_shortcut(gtk_shortcut)
        self._actions.pop(shortcut.name, None)

    def label(self, shortcut: Shortcut) -> str:
        return Gtk.accelerator_get_label(*self._accel(shortcut))

    def action_name(self, shortcut: Shortcut) -> str:
        return self._actions.get(shortcut.name, "")

    def _accel(self, shortcut: Shortcut) -> Tuple[int, Gdk.ModifierType]:
        accelerator = self._config.get(self._config.SHORTCUT_SECTION, shortcut.name, fallback=shortcut.value)
        return Gtk.accelerator_parse(accelerator)

    def _accel_str(self, shortcut: Shortcut) -> str:
        return self._config.get(self._config.SHORTCUT_SECTION, shortcut.name, fallback=shortcut.value)
