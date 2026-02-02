import locale
import logging
from locale import gettext as _

from gi.repository import Gio, Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Events, Session, SessionPayload, Subscriber, on
from tomate.ui import Shortcut, ShortcutEngine

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("tomate.ui.headerbar.menu", scope=SingletonScope)
class Menu(Subscriber):
    PREFERENCE_SHORTCUT = Shortcut("session.settings", "<control>comma")

    @inject(
        bus="tomate.bus",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(self, bus: Bus, shortcuts: ShortcutEngine):
        self.connect(bus)

        self.widget = Gio.Menu()
        self.widget.append_item(self._create_menu_item(_("Preferences"), "win.preferences"))
        self.widget.append_item(self._create_menu_item(_("About"), "win.about"))

        shortcuts.connect(Menu.PREFERENCE_SHORTCUT, "win.preferences")

    def _create_menu_item(self, label: str, action: str) -> Gio.MenuItem:
        return Gio.MenuItem.new(label, action)


@register.factory("tomate.ui.headerbar", scope=SingletonScope)
class HeaderBar(Subscriber):
    START_SHORTCUT = Shortcut("session.start", "<control>s")
    STOP_SHORTCUT = Shortcut("session.stop", "<control>p")
    RESET_SHORTCUT = Shortcut("session.reset", "<control>r")

    @inject(
        bus="tomate.bus",
        menu="tomate.ui.headerbar.menu",
        session="tomate.session",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(self, bus: Bus, menu: Menu, session: Session, shortcuts: ShortcutEngine):
        self.connect(bus)
        self._shortcuts = shortcuts
        self.widget = self._create_headerbar()

        self._start_button = self._add_button(
            "media-playback-start",
            "Starts the session",
            HeaderBar.START_SHORTCUT,
            lambda *_: session.start(),
        )

        self._stop_button = self._add_button(
            "media-playback-stop",
            "Stops the session",
            HeaderBar.STOP_SHORTCUT,
            lambda *_: session.stop(),
            visible=False,
        )

        self._reset_button = self._add_button(
            "edit-clear",
            "Clear session count",
            HeaderBar.RESET_SHORTCUT,
            lambda *_: session.reset(),
            sensitive=False,
        )

        self._add_preference_button(menu, shortcuts)

    def _create_headerbar(self):
        return Gtk.HeaderBar(
            show_close_button=True,
            title=_("No session yet"),
            decoration_layout=":close",
        )

    def _add_button(self, icon: str, tooltip_text: str, shortcut: Shortcut, on_clicked, **props) -> Gtk.Button:
        image = Gtk.Image.new_from_icon_name(icon)
        image.set_pixel_size(16)

        button = Gtk.Button(
            tooltip_text=_("{} ({})".format(tooltip_text, self._shortcuts.label(shortcut))), name=shortcut.name, **props
        )
        button.set_child(image)
        button.connect("clicked", on_clicked)

        self.widget.pack_start(button)
        self._shortcuts.connect(shortcut, "win.session-{}".format(shortcut.name.split(".")[-1]))

        return button

    def _add_preference_button(self, menu, shortcuts) -> None:
        icon = Gtk.Image.new_from_icon_name("preferences-system")
        icon.set_pixel_size(16)
        button = Gtk.MenuButton(
            name=Menu.PREFERENCE_SHORTCUT.name,
            tooltip_text=_("Open preferences ({})".format(shortcuts.label(Menu.PREFERENCE_SHORTCUT))),
        )
        button.set_menu_model(menu.widget)
        button.set_child(icon)
        self.widget.pack_end(button)

    @on(Events.SESSION_START)
    def _on_session_start(self, **__):
        logger.debug("action=enable_stop")
        self._start_button.props.visible = False
        self._stop_button.props.visible = True
        self._reset_button.props.sensitive = False

    @on(Events.SESSION_INTERRUPT, Events.SESSION_END)
    def _on_session_stop(self, payload: SessionPayload) -> None:
        logger.debug("action=enable_start pomodoros=%d", payload.pomodoros)
        self._start_button.props.visible = True
        self._stop_button.props.visible = False
        self._reset_button.props.sensitive = bool(payload.pomodoros)
        self._update_title(payload.pomodoros)

    @on(Events.SESSION_RESET)
    def _on_session_reset(self, **__):
        logger.debug("action=disable_reset")
        self._reset_button.props.sensitive = False
        self._update_title(0)

    def _update_title(self, pomodoros: int) -> None:
        self.widget.props.title = _("Session {}".format(pomodoros)) if pomodoros else _("No session yet")
