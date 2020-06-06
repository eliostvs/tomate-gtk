import locale
from locale import gettext as _

from gi.repository import Gtk
from wiring import inject, SingletonScope
from wiring.scanning import register

from tomate.pomodoro import State
from tomate.pomodoro.event import Subscriber, Events, on
from tomate.pomodoro.session import Payload as SessionPayload, Session
from tomate.ui.shortcut import ShortcutManager

locale.textdomain("tomate")


@register.factory("tomate.ui.headerbar.menu", scope=SingletonScope)
class Menu:
    @inject(
        about="tomate.ui.about",
        preference="tomate.ui.preference",
        lazy_proxy="tomate.proxy",
    )
    def __init__(self, about, preference, lazy_proxy):
        self._window = lazy_proxy("tomate.ui.view")

        self.widget = Gtk.Menu(halign=Gtk.Align.CENTER)

        self._preference_item = self._create_menu_item(
            _("Preferences"), preference.widget
        )
        self.widget.add(self._preference_item)

        self._about_item = self._create_menu_item(_("About"), about.widget)
        self.widget.add(self._about_item)

        self.widget.show_all()

    def _create_menu_item(self, label: str, dialog) -> Gtk.MenuItem:
        menu_item = Gtk.MenuItem.new_with_label(label)
        menu_item.connect("activate", self._show_dialog, dialog)

        return menu_item

    def _show_dialog(self, _, dialog: Gtk.Dialog) -> None:
        dialog.set_transient_for(self._window.widget)
        dialog.run()


@register.factory("tomate.ui.headerbar", scope=SingletonScope)
class HeaderBar(Subscriber):
    @inject(
        session="tomate.session",
        menu="tomate.ui.headerbar.menu",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(self, session: Session, menu: Menu, shortcuts: ShortcutManager):
        self._session = session
        self._shortcuts = shortcuts

        self.widget = Gtk.HeaderBar(
            show_close_button=True,
            title=_("No session yet"),
            decoration_layout=":close",
        )

        self._start_button = self._create_button(
            Gtk.STOCK_MEDIA_PLAY,
            "Starts the session",
            self._start_session,
            shortcuts.START,
        )
        self.widget.pack_start(self._start_button)

        self._stop_button = self._create_button(
            Gtk.STOCK_MEDIA_STOP,
            "Stops the session",
            self._stop_session,
            shortcuts.STOP,
            visible=False,
            no_show_all=True,
        )
        self.widget.pack_start(self._stop_button)

        self._reset_button = self._create_button(
            Gtk.STOCK_CLEAR,
            "Clear the count of sessions",
            self._reset_session,
            shortcuts.RESET,
            sensitive=False,
        )
        self.widget.pack_start(self._reset_button)

        button = Gtk.MenuButton(popup=menu.widget)
        icon = Gtk.Image.new_from_icon_name(Gtk.STOCK_PREFERENCES, Gtk.IconSize.BUTTON)
        button.add(icon)

        self.widget.pack_end(button)

    def _start_session(self, *args):
        self._session.start()

    def _stop_session(self, *args):
        self._session.stop()

    def _reset_session(self, *args):
        self._session.reset()

    @on(Events.Session, [State.started])
    def _on_session_started(self, *args, **kwargs):
        self._start_button.set_visible(False)
        self._stop_button.set_visible(True)
        self._reset_button.set_sensitive(False)

    @on(Events.Session, [State.stopped, State.finished])
    def _on_session_end(self, _, payload: SessionPayload):
        self._start_button.set_visible(True)
        self._stop_button.set_visible(False)
        self._reset_button.set_sensitive(bool(payload.pomodoros))
        self._update_title(payload.pomodoros)

    @on(Events.Session, [State.reset])
    def _on_session_reset(self, *args, **kwargs):
        self._reset_button.set_sensitive(False)

        self._update_title(0)

    def _update_title(self, pomodoros: int):
        self.widget.props.title = (
            _("Session {}".format(pomodoros)) if pomodoros > 0 else _("No session yet")
        )

    def _create_button(
        self, icon_name: str, tooltip_text: str, on_clicked, shortcut_name: str, **props
    ) -> Gtk.Button:
        image = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
        image.show()

        tooltip = "{} ({})".format(
            _(tooltip_text), self._shortcuts.label(shortcut_name)
        )
        button = Gtk.Button(tooltip_text=tooltip, **props)
        button.add(image)
        button.connect("clicked", on_clicked)

        self._shortcuts.connect(shortcut_name, on_clicked)

        return button
