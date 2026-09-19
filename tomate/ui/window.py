import logging
import time

from gi.repository import GdkPixbuf, Gtk

from tomate.pomodoro.config import Config
from tomate.pomodoro.event import Bus, Event, Events, Subscriber, on
from tomate.pomodoro.graph import Injected
from tomate.pomodoro.plugin import PluginEngine
from tomate.pomodoro.session import Payload as SessionPayload
from tomate.pomodoro.session import Session

from .dialogs import AboutDialog, ExtensionTab, PreferenceDialog, TimerTab
from .shortcut import ShortcutEngine
from .systray import SysTray
from .widgets import Countdown, HeaderBar, HeaderBarMenu, SessionButton

logger = logging.getLogger(__name__)


class Window(Subscriber):
    def __init__(
        self,
        bus: Injected[Bus],
        config: Injected[Config],
        session: Injected[Session],
        plugin_engine: Injected[PluginEngine],
        systray: Injected[SysTray],
    ) -> None:
        self._session = session
        self._bus = bus
        self._systray = systray
        countdown = Countdown(bus)
        shortcuts = ShortcutEngine(config)
        session_button = SessionButton(bus, session, shortcuts)
        about = AboutDialog(config)
        timer_tab = TimerTab(config)
        extension_tab = ExtensionTab(bus, config, plugin_engine)
        preference = PreferenceDialog(timer_tab, extension_tab)
        menu = HeaderBarMenu(bus, about, preference, shortcuts)
        headerbar = HeaderBar(bus, menu, session, shortcuts)
        content = self._create_content(countdown, session_button)
        self.widget = self._create_window(config, headerbar, content)

        shortcuts.init(self.widget)
        self.connect(bus)
        session.ready()

    def _create_window(self, config: Config, headerbar: HeaderBar, box: Gtk.Box) -> Gtk.Window:
        window = Gtk.Window(
            title="Tomate",
            icon=GdkPixbuf.Pixbuf.new_from_file(config.icon_path("tomate", 22)),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )
        window.set_size_request(350, -1)
        window.set_titlebar(headerbar.widget)
        window.connect("delete-event", self.quit)
        window.add(box)
        return window

    def _create_content(self, countdown: Countdown, session_button: SessionButton) -> Gtk.Box:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.pack_start(countdown.widget, False, False, 0)
        box.pack_start(session_button.widget, False, False, 0)
        return box

    def run(self) -> None:
        logger.debug("action=run")
        self.widget.show_all()
        Gtk.main()

    def quit(self, *_) -> None:
        if self._session.is_running():
            return self.hide()
        else:
            logger.debug("action=quit")
            Gtk.main_quit()

    def hide(self):
        self._bus.publish(Events.WINDOW_HIDE)

        if self._systray.available:
            logger.debug("action=hide strategy=tray")
            return self.widget.hide_on_delete()
        else:
            logger.debug("action=hide strategy=minimize")
            self.widget.iconify()
            return Gtk.true

    @on(Events.SESSION_END)
    def show(self, _event: Event[SessionPayload] | None = None) -> None:
        logger.debug("action=show")
        self._bus.publish(Events.WINDOW_SHOW)
        self.widget.present_with_time(int(time.time()))
