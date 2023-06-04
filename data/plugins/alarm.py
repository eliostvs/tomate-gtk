import logging
from locale import gettext as _
from os import path
from urllib.parse import urlparse

import gi
from wiring import Graph

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

import tomate.pomodoro.plugin as plugin
from tomate.audio import GStreamerPlayer
from tomate.pomodoro import Bus, Config, Events, on, suppress_errors

logger = logging.getLogger(__name__)

SECTION_NAME = "alarm_plugin"
OPTION_NAME = "uri"


class AlarmPlugin(plugin.Plugin):
    has_settings = True

    @suppress_errors
    def __init__(self):
        super().__init__()
        self.config = None
        self.player = None

    def configure(self, bus: Bus, graph: Graph) -> None:
        super().configure(bus, graph)
        self.config = graph.get("tomate.config")

    @suppress_errors
    def activate(self) -> None:
        super().activate()
        logger.debug("action=activate uri=%s volume=%f", self.audio_path, self.volume)
        self.player = GStreamerPlayer(repeat=False)
        self.player.file = self.audio_path
        self.player.volume = self.volume

    @suppress_errors
    def deactivate(self) -> None:
        super().deactivate()
        logger.debug("action=deactivate")

        if self.player:
            self.player.stop()

    @suppress_errors
    @on(Events.SESSION_END)
    def on_end(self, **__) -> None:
        logger.debug("action=on_end")
        if self.player:
            self.player.play()

    @property
    def audio_path(self) -> str:
        return self.config.get(SECTION_NAME, OPTION_NAME, fallback=self.config.media_uri("alarm.ogg"))

    @property
    def volume(self) -> float:
        return self.config.get_float(SECTION_NAME, "volume", fallback=1.0)

    def settings_window(self, toplevel: Gtk.Dialog) -> "SettingsDialog":
        return SettingsDialog(self.config, toplevel)


class SettingsDialog:
    def __init__(self, config: Config, toplevel: Gtk.Dialog):
        self.config = config
        self.widget = self.create_dialog(toplevel)

    def create_dialog(self, toplevel: Gtk.Dialog) -> Gtk.Dialog:
        dialog = Gtk.Dialog(
            border_width=12,
            modal=True,
            resizable=False,
            title=_("Preferences"),
            transient_for=toplevel,
            window_position=Gtk.WindowPosition.CENTER_ON_PARENT,
        )
        dialog.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        dialog.connect("response", lambda widget, _: widget.destroy())
        dialog.set_size_request(350, -1)
        dialog.get_content_area().add(self.create_options())
        return dialog

    def create_options(self) -> Gtk.Grid:
        custom_audio = self.config.get(SECTION_NAME, OPTION_NAME, fallback="")

        grid = Gtk.Grid(column_spacing=12, row_spacing=12, margin_bottom=12, margin_top=12)
        label = Gtk.Label(label=_("Custom:"), hexpand=True, halign=Gtk.Align.END)
        grid.attach(label, 0, 0, 1, 1)

        entry = self.create_custom_alarm_input(custom_audio)
        grid.attach(entry, 0, 1, 4, 1)

        switch = self.create_custom_alarm_switch(custom_audio, entry)
        grid.attach_next_to(switch, label, Gtk.PositionType.RIGHT, 1, 1)

        return grid

    def create_custom_alarm_input(self, custom_audio) -> Gtk.Entry:
        entry = Gtk.Entry(
            editable=False,
            hexpand=True,
            name="custom_entry",
            secondary_icon_activatable=True,
            secondary_icon_name=Gtk.STOCK_FILE,
            sensitive=bool(custom_audio),
            text=custom_audio,
        )
        entry.connect("icon-press", self.select_custom_alarm)
        entry.connect("notify::text", self.custom_alarm_changed)
        return entry

    def create_custom_alarm_switch(self, custom_audio, entry) -> Gtk.Switch:
        switch = Gtk.Switch(
            hexpand=True,
            halign=Gtk.Align.START,
            active=bool(custom_audio),
            name="custom_switch",
        )
        switch.connect("notify::active", self.custom_alarm_toggle, entry)
        return switch

    def select_custom_alarm(self, entry: Gtk.Entry, *_) -> None:
        dialog = self.create_file_chooser(self.dirname(entry.props.text))
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_uri())

        dialog.destroy()

    def dirname(self, audio_path: str) -> str:
        return path.dirname(urlparse(audio_path).path) if audio_path else path.expanduser("~")

    def create_file_chooser(self, current_folder: str) -> Gtk.FileChooserDialog:
        dialog = Gtk.FileChooserDialog(
            _("Please choose a file"),
            self.widget,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )
        dialog.add_filter(self.create_filter("audio/mp3", "audio/mpeg"))
        dialog.add_filter(self.create_filter("audio/ogg", "audio/ogg"))
        dialog.set_current_folder(current_folder)
        return dialog

    @staticmethod
    def create_filter(name: str, mime_type: str) -> Gtk.FileFilter:
        mime_type_filter = Gtk.FileFilter()
        mime_type_filter.set_name(name)
        mime_type_filter.add_mime_type(mime_type)
        return mime_type_filter

    def custom_alarm_changed(self, entry: Gtk.Entry, _) -> None:
        custom_alarm = entry.props.text

        if custom_alarm:
            logger.debug("action=set_option section=%s option=%s value", SECTION_NAME, OPTION_NAME)
            self.config.set(SECTION_NAME, OPTION_NAME, custom_alarm)
        else:
            logger.debug("action=remove_option section=%s option=%s", SECTION_NAME, OPTION_NAME)
            self.config.remove(SECTION_NAME, OPTION_NAME)

    @staticmethod
    def custom_alarm_toggle(switch: Gtk.Switch, _, entry: Gtk.Entry) -> None:
        if switch.props.active:
            entry.set_properties(sensitive=True)
        else:
            entry.set_properties(text="", sensitive=False)

    def run(self) -> Gtk.Dialog:
        self.widget.show_all()
        return self.widget
