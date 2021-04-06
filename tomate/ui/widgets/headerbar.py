import locale
import logging
from collections import namedtuple
from locale import gettext as _
from typing import Union

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro.event import Events, Subscriber, on
from tomate.pomodoro.session import EndPayload as SessionEndPayload, Payload as SessionPayload, Session
from tomate.ui.shortcut import ShortcutManager

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("tomate.ui.headerbar.menu", scope=SingletonScope)
class Menu(Subscriber):
    @inject(about="tomate.ui.about", bus="tomate.bus", lazy_proxy="tomate.proxy", preference="tomate.ui.preference")
    def __init__(self, about, bus, lazy_proxy, preference):
        self.connect(bus)
        self._window = lazy_proxy("tomate.ui.view")

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self._preference_item = self._create_menu_item(_("Preferences"), preference.widget)
        self.widget.add(self._preference_item)

        self._about_item = self._create_menu_item(_("About"), about.widget)
        self.widget.add(self._about_item)

        self.widget.show_all()

    def _create_menu_item(self, label: str, dialog) -> Gtk.MenuItem:
        menu_item = Gtk.MenuItem.new_with_label(label)
        menu_item.connect("activate", self._open_dialog, dialog)

        return menu_item

    def _open_dialog(self, _, dialog: Gtk.Dialog) -> None:
        logger.debug("action=open_dialog")
        dialog.set_transient_for(self._window.widget)
        dialog.run()


Shortcut = namedtuple("Shortcut", "name default")


@register.factory("tomate.ui.headerbar", scope=SingletonScope)
class HeaderBar(Subscriber):
    @inject(
        bus="tomate.bus",
        menu="tomate.ui.headerbar.menu",
        session="tomate.session",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(self, bus, menu: Menu, session: Session, shortcuts: ShortcutManager):
        self._session = session
        self.shortcuts = shortcuts
        self.connect(bus)

        self.widget = Gtk.HeaderBar(
            show_close_button=True,
            title=_("No session yet"),
            decoration_layout=":close",
        )

        self._start_button = self._create_button(
            Gtk.STOCK_MEDIA_PLAY,
            "Starts the session",
            lambda *_: self._session.start(),
            Shortcut(name="button.start", default="<control>s"),
        )
        self.widget.pack_start(self._start_button)

        self._stop_button = self._create_button(
            Gtk.STOCK_MEDIA_STOP,
            "Stops the session",
            lambda *_: self._session.stop(),
            Shortcut(name="button.stop", default="<control>p"),
            visible=False,
            no_show_all=True,
        )
        self.widget.pack_start(self._stop_button)

        self._reset_button = self._create_button(
            Gtk.STOCK_CLEAR,
            "Clear the count of sessions",
            lambda *_: self._session.reset(),
            Shortcut(name="button.reset", default="<control>r"),
            sensitive=False,
        )
        self.widget.pack_start(self._reset_button)

        button = Gtk.MenuButton(popup=menu.widget)
        icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_PREFERENCES, Gtk.IconSize.BUTTON)
        button.add(icon)

        self.widget.pack_end(button)

    @on(Events.SESSION_START)
    def _on_session_start(self, *_, **__):
        logger.debug("action=enable_stop")
        self._start_button.set_visible(False)
        self._stop_button.set_visible(True)
        self._reset_button.set_sensitive(False)

    @on(Events.SESSION_INTERRUPT, Events.SESSION_END)
    def _on_session_stop(self, _, payload: Union[SessionEndPayload, SessionPayload]) -> None:
        logger.debug("action=enable_start pomodoros=%d", payload.pomodoros)
        self._start_button.set_visible(True)
        self._stop_button.set_visible(False)
        self._reset_button.set_sensitive(bool(payload.pomodoros))
        self._update_title(payload.pomodoros)

    @on(Events.SESSION_RESET)
    def _on_session_reset(self, *_, **__):
        logger.debug("action=disable_reset")
        self._reset_button.set_sensitive(False)
        self._update_title(0)

    def _update_title(self, pomodoros: int) -> None:
        self.widget.props.title = _("Session {}".format(pomodoros)) if pomodoros else _("No session yet")

    def _create_button(self, icon_name: str, tooltip_text: str, on_clicked, shortcut: Shortcut, **props) -> Gtk.Button:
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        image.show()

        tooltip = "{} ({})".format(_(tooltip_text), self.shortcuts.label(shortcut.name, shortcut.default))
        button = Gtk.Button(tooltip_text=tooltip, **props)
        button.add(image)
        button.connect("clicked", on_clicked)

        self.shortcuts.connect(shortcut.name, on_clicked, shortcut.default)

        return button
