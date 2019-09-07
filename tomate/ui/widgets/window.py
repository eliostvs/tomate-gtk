import logging
import time

from gi.repository import GdkPixbuf, Gtk
from wiring import inject, Graph, SingletonScope
from wiring.scanning import register

from tomate.core import State
from tomate.core.event import Subscriber, on, Events
from tomate.ui.widgets.systray import TrayIcon

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.view", scope=SingletonScope)
class Window(Subscriber):
    @inject(
        session="tomate.session",
        dispatcher="tomate.events.view",
        config="tomate.config",
        graph=Graph,
        headerbar="tomate.ui.headerbar",
        countdown="tomate.ui.countdown",
        task_button="tomate.ui.taskbutton",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(
        self,
        session,
        dispatcher,
        config,
        graph,
        headerbar,
        countdown,
        task_button,
        shortcuts,
    ):
        self._config = config
        self._session = session
        self._dispatcher = dispatcher
        self._graph = graph

        self.widget = Gtk.Window(
            title="Tomate",
            icon=GdkPixbuf.Pixbuf.new_from_file(
                self._config.get_icon_path("tomate", 22)
            ),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )

        self.widget.set_size_request(350, -1)
        self.widget.set_titlebar(headerbar.widget)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.pack_start(countdown.widget, False, False, 0)
        box.pack_start(task_button.widget, False, False, 0)

        self.widget.add(box)

        # TODO: this connect
        self.widget.connect("delete-event", lambda *args: self.quit())

        self.widget.show_all()

        shortcuts.initialize(self.widget)

        task_button.enable()

    def run(self, *args, **kwargs):
        Gtk.main()

    def quit(self, *args, **kwargs):
        if self._session.is_running():
            return self.hide()
        else:
            logger.debug("action=quit")
            Gtk.main_quit()

    @on(Events.Session, [State.finished])
    def show(self, *args, **kwargs):
        self._dispatcher.send(State.showed)

        logger.debug("action=show")

        self.widget.present_with_time(time.time())

    def hide(self, *args, **kwargs):
        self._dispatcher.send(State.hid)

        if TrayIcon in self._graph.providers:
            logger.debug("action=hide to=tray")
            return self.widget.hide_on_delete()
        else:
            logger.debug("action=hide to=minimize")
            self.widget.iconify()
            return Gtk.true
