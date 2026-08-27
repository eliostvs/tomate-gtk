from gi.repository import Gtk

from tomate.pomodoro import Event, Events, on, plugin


class PluginA(plugin.Plugin):
    has_settings = True

    def __init__(self):
        super().__init__()
        self.parent = None

    @on(Events.WINDOW_SHOW)
    def listener(self, _event: Event[None]) -> str:
        self.last_event = _event
        return "plugin_a"

    def settings_window(self, parent: Gtk.Widget) -> Gtk.Dialog:
        self.parent = parent
        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.INFO,
            transient_for=parent,
            buttons=Gtk.ButtonsType.OK,
            text="Plugin A Settings",
        )
        dialog.connect("response", lambda widget, _: widget.destroy())
        return dialog
