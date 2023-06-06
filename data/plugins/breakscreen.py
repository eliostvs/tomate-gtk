import logging
from collections import namedtuple
from locale import gettext as _
from typing import Dict

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")

from gi.repository import Gdk, GLib, Gtk

import tomate.pomodoro.plugin as plugin
from tomate.pomodoro import (Config, ConfigPayload, Events, Session,
                             SessionPayload, SessionType, Subscriber, Timer,
                             TimerPayload, on, suppress_errors)

logger = logging.getLogger(__name__)

SECTION_NAME = "break_screen"
SKIP_BREAK_OPTION = "skip_break"
AUTO_START_OPTION = "auto_start"


class Monitor(namedtuple("Monitor", "number geometry")):
    @property
    def x(self) -> int:
        return self.geometry.x

    @property
    def y(self) -> int:
        return self.geometry.y

    @property
    def width(self) -> int:
        return self.geometry.width

    @property
    def height(self) -> int:
        return self.geometry.height


class BreakScreen(Subscriber):
    def __init__(self, monitor: Monitor, session: Session, config: Config):
        logger.debug("action=init_screen monitor=%s", monitor)

        self.monitor = monitor
        self.session = session
        self.options = self.create_options(config)
        self.countdown = Gtk.Label(label="00:00", name="countdown")
        self.skip_button = self.create_button()
        content = self.create_content_area(self.countdown, self.skip_button)
        self.widget = self.create_window(self.monitor, content)

    def create_options(self, config) -> Dict[str, bool]:
        return {
            SKIP_BREAK_OPTION: config.get_bool(SECTION_NAME, SKIP_BREAK_OPTION, fallback=False),
            AUTO_START_OPTION: config.get_bool(SECTION_NAME, AUTO_START_OPTION, fallback=False),
        }

    def create_button(self) -> Gtk.Button:
        logger.debug("action=create_skip_button visibile=%s", self.options[SKIP_BREAK_OPTION])
        button = Gtk.Button(label=_("Skip"), name="skip", visible=self.options[SKIP_BREAK_OPTION], no_show_all=True)
        button.connect("clicked", self.skip_break)
        button.grab_focus()
        return button

    def skip_break(self, _) -> None:
        logger.debug("action=skip_break")
        self.session.stop()
        self.session.change(SessionType.POMODORO)

    def create_content_area(self, countdown: Gtk.Label, skip_button: Gtk.Button) -> Gtk.Box:
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content.pack_start(countdown, False, False, 0)
        content.pack_start(skip_button, False, False, 0)

        space = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
        space.pack_start(content, True, True, 0)
        return space

    def create_window(self, monitor: Monitor, box: Gtk.Box) -> Gtk.Window:
        window = Gtk.Window(
            can_focus=False,
            decorated=False,
            deletable=False,
            focus_on_map=False,
            gravity=Gdk.Gravity.CENTER,
            name="breakscreen",
            skip_taskbar_hint=True,
            urgency_hint=True,
        )
        window.set_visual(window.get_screen().get_rgba_visual())
        window.stick()
        window.set_keep_above(True)
        window.fullscreen()
        window.move(monitor.x, monitor.y)
        window.resize(monitor.width, monitor.height)
        window.add(box)
        return window

    @on(Events.SESSION_START)
    def on_session_start(self, payload=SessionPayload) -> None:
        logger.debug("action=session_start monitor=%d session=%s", self.monitor.number, payload.type)

        if payload.type != SessionType.POMODORO:
            self.countdown.set_text(payload.countdown)
            self.widget.show_all()

    @on(Events.SESSION_INTERRUPT)
    def on_session_interrupt(self, **__) -> None:
        logger.debug("action=session_start monitor=%d", self.monitor.number)
        self.widget.hide()

    @on(Events.SESSION_END)
    def on_session_end(self, payload: SessionPayload) -> None:
        logger.debug(
            "action=session_end monitor=%d auto_start=%s session_type=%s",
            self.monitor.number,
            self.auto_start,
            payload.type,
        )

        if payload.type == SessionType.POMODORO and self.auto_start:
            GLib.timeout_add_seconds(Timer.ONE_SECOND, self._start_session)
        else:
            self.widget.hide()

    def _start_session(self) -> bool:
        self.session.start()
        return False

    @property
    def auto_start(self) -> bool:
        return self.options[AUTO_START_OPTION]

    @on(Events.TIMER_UPDATE)
    def on_timer_update(self, payload: TimerPayload) -> None:
        logger.debug("action=update_countdown monitor=%s countdown=%s", payload.countdown, self.monitor.number)
        self.countdown.set_text(payload.countdown)

    @on(Events.CONFIG_CHANGE)
    def on_settings_change(self, payload: ConfigPayload) -> None:
        if payload.section != SECTION_NAME:
            return

        logger.debug(
            "action=change_option monitor=%d config=%s option=%s",
            self.monitor.number,
            payload.action,
            payload.option,
        )
        self.options[payload.option] = payload.action == "set"
        self.skip_button.props.visible = self.options[SKIP_BREAK_OPTION]


class SettingsDialog:
    def __init__(self, config: Config, toplevel):
        self.options = {SKIP_BREAK_OPTION: False, AUTO_START_OPTION: False}
        self.config = config
        self.widget = self.create_dialog(toplevel)

    def create_dialog(self, toplevel) -> Gtk.Dialog:
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

    def create_options(self):
        grid = Gtk.Grid(column_spacing=12, row_spacing=12, margin_bottom=12, margin_top=12)
        self.create_option(grid, 0, _("Auto start:"), AUTO_START_OPTION)
        self.create_option(grid, 1, _("Skip break:"), SKIP_BREAK_OPTION)
        return grid

    def run(self):
        self.widget.show_all()
        return self.widget

    def create_option(self, grid: Gtk.Grid, row: int, label: str, option):
        active = self.config.get_bool(SECTION_NAME, option, fallback=False)
        self.options[option] = active

        label = Gtk.Label(label=_(label), hexpand=True, halign=Gtk.Align.END)
        grid.attach(label, 0, row, 1, 1)

        switch = Gtk.Switch(hexpand=True, halign=Gtk.Align.START, name=option, active=active)
        switch.connect("notify::active", self.on_option_change, option)
        grid.attach_next_to(switch, label, Gtk.PositionType.RIGHT, 1, 1)

    def on_option_change(self, switch: Gtk.Switch, _, option: str):
        self.options[option] = switch.props.active

        if switch.props.active:
            self.config.set(SECTION_NAME, option, "true")
        else:
            logger.debug("action=remove_option name=%s", option)
            self.config.remove(SECTION_NAME, option)


class BreakScreenPlugin(plugin.Plugin):
    has_settings = True

    @suppress_errors
    def __init__(self, display=Gdk.Display.get_default()):
        super().__init__()
        self.display = display
        self.screens = []
        self.configure_style()

    @staticmethod
    def configure_style():
        style = b"""
        #breakscreen {
            background-color: #1c1c1c;
        }

        #skip {
            color: white;
            font-size: 1.5em;
            font-weight: 900;
            background: transparent;
            border-color: white;
            border-image: none;
            border-radius: 25px;
            border-width: 2px;
            padding-bottom: 10px;
            padding-left: 25px;
            padding-right: 25px;
            padding-top: 10px;
        }

        #skip:hover, #skip:active {
            background: white;
            color: black;
        }

        #countdown {
            font-size: 10em;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(style)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    @suppress_errors
    def activate(self):
        super().activate()

        for monitor in range(self.display.get_n_monitors()):
            geometry = self.display.get_monitor(monitor).get_geometry()
            screen = BreakScreen(
                Monitor(monitor, geometry), self.graph.get("tomate.session"), self.graph.get("tomate.config")
            )
            screen.connect(self.bus)
            self.screens.append(screen)

    @suppress_errors
    def deactivate(self):
        super().deactivate()

        for screen in self.screens:
            screen.disconnect(self.bus)
            screen.widget.destroy()

        del self.screens[:]

    def settings_window(self, toplevel) -> SettingsDialog:
        return SettingsDialog(self.graph.get("tomate.config"), toplevel)
