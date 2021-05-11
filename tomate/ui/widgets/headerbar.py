import locale
import logging
from locale import gettext as _
from typing import Union

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Events, Session, SessionEndPayload, SessionPayload, Subscriber, on
from tomate.ui import Shortcut, ShortcutEngine

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("tomate.ui.headerbar.menu", scope=SingletonScope)
class Menu(Subscriber):
    PREFERENCE_SHORTCUT = Shortcut("session.settings", "<control>comma")

    @inject(
        bus="tomate.bus",
        about="tomate.ui.about",
        preference="tomate.ui.preference",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(self, bus: Bus, about, preference, shortcuts: ShortcutEngine):
        self.connect(bus)

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)
        self.widget.add(self._create_menu_item("header.menu.preference", _("Preferences"), preference.widget))
        self.widget.add(self._create_menu_item("header.menu.about", _("About"), about.widget))
        self.widget.show_all()

        shortcuts.connect(Menu.PREFERENCE_SHORTCUT, lambda *_: preference.widget.run())

    def _create_menu_item(self, name: str, label: str, dialog: Gtk.Dialog) -> Gtk.MenuItem:
        menu_item = Gtk.MenuItem.new_with_label(label)
        menu_item.props.name = name
        menu_item.connect("activate", lambda *_: dialog.run())
        return menu_item


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
            Gtk.STOCK_MEDIA_PLAY,
            "Starts the session",
            HeaderBar.START_SHORTCUT,
            lambda *_: session.start(),
        )

        self._stop_button = self._add_button(
            Gtk.STOCK_MEDIA_STOP,
            "Stops the session",
            HeaderBar.STOP_SHORTCUT,
            lambda *_: session.stop(),
            no_show_all=True,
            visible=False,
        )

        self._reset_button = self._add_button(
            Gtk.STOCK_CLEAR,
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
        image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
        image.show()

        button = Gtk.Button(
            tooltip_text=_("{} ({})".format(tooltip_text, self._shortcuts.label(shortcut))), name=shortcut.name, **props
        )
        button.add(image)
        button.connect("clicked", on_clicked)

        self.widget.pack_start(button)
        self._shortcuts.connect(shortcut, on_clicked)

        return button

    def _add_preference_button(self, menu, shortcuts) -> None:
        icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_PREFERENCES, Gtk.IconSize.BUTTON)
        button = Gtk.MenuButton(
            name=Menu.PREFERENCE_SHORTCUT.name,
            popup=menu.widget,
            tooltip_text=_("Open preferences ({})".format(shortcuts.label(Menu.PREFERENCE_SHORTCUT))),
        )
        button.add(icon)
        self.widget.pack_end(button)

    @on(Events.SESSION_START)
    def _on_session_start(self, *_, **__):
        logger.debug("action=enable_stop")
        self._start_button.props.visible = False
        self._stop_button.props.visible = True
        self._reset_button.props.sensitive = False

    @on(Events.SESSION_INTERRUPT, Events.SESSION_END)
    def _on_session_stop(self, _, payload: Union[SessionEndPayload, SessionPayload]) -> None:
        logger.debug("action=enable_start pomodoros=%d", payload.pomodoros)
        self._start_button.props.visible = True
        self._stop_button.props.visible = False
        self._reset_button.props.sensitive = bool(payload.pomodoros)
        self._update_title(payload.pomodoros)

    @on(Events.SESSION_RESET)
    def _on_session_reset(self, *_, **__):
        logger.debug("action=disable_reset")
        self._reset_button.props.sensitive = False
        self._update_title(0)

    def _update_title(self, pomodoros: int) -> None:
        self.widget.props.title = _("Session {}".format(pomodoros)) if pomodoros else _("No session yet")
