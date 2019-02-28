import logging
import time

from gi.repository import GdkPixbuf, Gtk
from tomate.constant import State
from tomate.event import Subscriber, on, Events
from tomate.view import UI, TrayIcon
from wiring import implements, inject, Graph, SingletonScope
from wiring.scanning import register

logger = logging.getLogger(__name__)


@register.factory("tomate.view", scope=SingletonScope)
@implements(UI)
class GtkUI(Subscriber):
    @inject(
        session="tomate.session",
        dispatcher="tomate.events.view",
        config="tomate.config",
        graph=Graph,
        headerbar="view.headerbar",
        countdown="view.countdown",
        task_button="view.taskbutton",
        shortcuts="view.shortcut",
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
        self.config = config
        self.session = session
        self.dispatcher = dispatcher
        self.graph = graph

        self.widget = Gtk.Window(
            title="Tomate",
            icon=GdkPixbuf.Pixbuf.new_from_file(
                self.config.get_icon_path("tomate", 22)
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
        if self.session.is_running():
            return self.hide()
        else:
            logger.debug("component=view acton=quit")
            Gtk.main_quit()

    @on(Events.Session, [State.finished])
    def show(self, *args, **kwargs):
        self.dispatcher.send(State.showed)

        logger.debug("component=view acton=show")

        self.widget.present_with_time(time.time())

    def hide(self, *args, **kwargs):
        self.dispatcher.send(State.hid)

        if TrayIcon in self.graph.providers.keys():
            logger.debug("component=view action=hide to=tray")
            return self.widget.hide_on_delete()
        else:
            logger.debug("component=view action=hide to=minimize")
            self.widget.iconify()
            return Gtk.true
