import logging
import time

from gi.repository import GdkPixbuf, Gtk
from wiring import Graph, SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Config, Events, Session, Subscriber, on

from .shortcut import ShortcutEngine
from .systray import Systray
from .widgets import Countdown, HeaderBar, SessionButton

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.view", scope=SingletonScope)
class Window(Subscriber):
    @inject(
        bus="tomate.bus",
        config="tomate.config",
        countdown="tomate.ui.countdown",
        graph=Graph,
        headerbar="tomate.ui.headerbar",
        session="tomate.session",
        session_button="tomate.ui.taskbutton",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(
        self,
        bus: Bus,
        config: Config,
        countdown: Countdown,
        graph: Graph,
        headerbar: HeaderBar,
        session: Session,
        session_button: SessionButton,
        shortcuts: ShortcutEngine,
    ):
        self._session = session
        self._bus = bus
        self._graph = graph
        self.connect(bus)

        content = self._create_content(countdown, session_button)
        self.widget = self._create_window(config, headerbar, content)

        shortcuts.init(self.widget)
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
        self._bus.send(Events.WINDOW_HIDE)

        if Systray in self._graph.providers:
            logger.debug("action=hide strategy=tray")
            return self.widget.hide_on_delete()
        else:
            logger.debug("action=hide strategy=minimize")
            self.widget.iconify()
            return Gtk.true

    @on(Events.SESSION_END)
    def show(self, **__) -> None:
        logger.debug("action=show")
        self._bus.send(Events.WINDOW_SHOW)
        self.widget.present_with_time(time.time())
