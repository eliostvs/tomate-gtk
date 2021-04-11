import locale
import logging
from locale import gettext as _
from typing import Union

import blinker
from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Events, Session, SessionEndPayload, SessionPayload, Subscriber, on
from tomate.ui import Shortcut, ShortcutEngine

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("tomate.ui.headerbar.menu", scope=SingletonScope)
class Menu(Subscriber):
    @inject(
        bus="tomate.bus",
        about="tomate.ui.about",
        preference="tomate.ui.preference",
    )
    def __init__(self, bus: blinker.signal, about, preference):
        self.connect(bus)

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)
        self.widget.add(self._create_menu_item("header.menu.preference", _("Preferences"), preference.widget))
        self.widget.add(self._create_menu_item("header.menu.about", _("About"), about.widget))
        self.widget.show_all()

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
    def __init__(self, bus: blinker.Signal, menu: Menu, session: Session, shortcuts: ShortcutEngine):
        self.connect(bus)

        self.widget = Gtk.HeaderBar(
            show_close_button=True,
            title=_("No session yet"),
            decoration_layout=":close",
        )

        self._start_button = self._create_button(
            Gtk.STOCK_MEDIA_PLAY,
            ("Starts the session ({})".format(shortcuts.label(HeaderBar.START_SHORTCUT))),
            lambda *_: session.start(),
            name=HeaderBar.START_SHORTCUT.name,
        )
        self.widget.pack_start(self._start_button)
        shortcuts.connect(HeaderBar.START_SHORTCUT, lambda *_: session.start())

        self._stop_button = self._create_button(
            Gtk.STOCK_MEDIA_STOP,
            ("Stops the session ({})".format(shortcuts.label(HeaderBar.STOP_SHORTCUT))),
            lambda *_: session.stop(),
            name=HeaderBar.STOP_SHORTCUT.name,
            no_show_all=True,
            visible=False,
        )
        self.widget.pack_start(self._stop_button)
        shortcuts.connect(HeaderBar.STOP_SHORTCUT, lambda *_: session.stop())

        self._reset_button = self._create_button(
            Gtk.STOCK_CLEAR,
            ("Clear session count ({})".format(shortcuts.label(HeaderBar.RESET_SHORTCUT))),
            lambda *_: session.reset(),
            name=HeaderBar.RESET_SHORTCUT.name,
            sensitive=False,
        )
        self.widget.pack_start(self._reset_button)
        shortcuts.connect(HeaderBar.RESET_SHORTCUT, lambda *_: session.reset())

        button = Gtk.MenuButton(popup=menu.widget)
        icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_PREFERENCES, Gtk.IconSize.BUTTON)
        button.add(icon)

        self.widget.pack_end(button)

    def _create_button(self, icon: str, tooltip_text: str, on_clicked, **props) -> Gtk.Button:
        image = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
        image.show()

        button = Gtk.Button(tooltip_text=tooltip_text, **props)
        button.add(image)
        button.connect("clicked", on_clicked)
        return button

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
