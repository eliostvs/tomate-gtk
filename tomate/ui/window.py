import logging
import time

from gi.repository import GdkPixbuf, Gtk
from wiring import Graph, SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro.event import Events, Subscriber, on
from .systray import Systray

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
        bus,
        config,
        countdown,
        graph: Graph,
        headerbar,
        session,
        session_button,
        shortcuts,
    ):
        self._session = session
        self._bus = bus
        self._graph = graph
        self.connect(bus)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.pack_start(countdown.widget, False, False, 0)
        box.pack_start(session_button.widget, False, False, 0)

        self.widget = Gtk.Window(
            title="Tomate",
            icon=GdkPixbuf.Pixbuf.new_from_file(config.icon_path("tomate", 22)),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )
        self.widget.set_size_request(350, -1)
        self.widget.set_titlebar(headerbar.widget)
        self.widget.add(box)
        self.widget.connect("delete-event", self.quit)

        shortcuts.init(self.widget)
        session_button.init()

    def run(self):
        logger.debug("action=run")
        self.widget.show_all()
        Gtk.main()

    def quit(self, *_):
        if self._session.is_running():
            return self.hide()
        else:
            logger.debug("action=quit")
            Gtk.main_quit()

    def hide(self):
        self._bus.send(Events.WINDOW_HIDE)

        if Systray in self._graph.providers:
            logger.debug("action=hide to=tray")
            return self.widget.hide_on_delete()
        else:
            self.widget.iconify()
            logger.debug("action=hide to=minimize")
            return Gtk.true

    @on(Events.SESSION_END)
    def show(self, *_, **__):
        logger.debug("action=show")
        self._bus.send(Events.WINDOW_SHOW)
        self.widget.present_with_time(time.time())
