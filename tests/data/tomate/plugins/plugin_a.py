from gi.repository import Gtk

import tomate.pomodoro.plugin as plugin
from tomate.pomodoro import Events, on


class PluginA(plugin.Plugin):
    has_settings = True

    def __init__(self):
        super().__init__()
        self.parent = None

    @on(Events.WINDOW_SHOW)
    def event_listener(self, _) -> str:
        return "plugin_a"

    def settings_window(self, parent: Gtk.Widget) -> Gtk.Dialog:
        self.parent = parent
        return Gtk.Dialog()
