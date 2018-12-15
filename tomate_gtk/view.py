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
        event="tomate.events.view",
        config="tomate.config",
        graph=Graph,
        headerbar="view.headerbar",
        timer_frame="view.timerframe",
        task_button="view.taskbutton",
        infobar="view.infobar",
        task_entry="view.taskentry",
    )
    def __init__(
        self,
        session,
        event,
        config,
        graph,
        headerbar,
        timer_frame,
        task_button,
        infobar,
        task_entry,
    ):

        self.config = config
        self.session = session
        self.event = event
        self.graph = graph
        self.infobar = infobar.widget

        self.window = Gtk.Window(
            title="Tomate",
            icon=GdkPixbuf.Pixbuf.new_from_file(
                self.config.get_icon_path("tomate", 22)
            ),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False,
        )

        self.window.set_size_request(350, -1)
        self.window.set_titlebar(headerbar.widget)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.pack_start(self.infobar, False, False, 0)
        box.pack_start(timer_frame.widget, False, False, 0)
        box.pack_start(task_entry.widget, False, False, 0)
        box.pack_start(task_button.widget, False, False, 0)

        self.window.add(box)

        self.window.connect("delete-event", self._on_delete_event)

        self.window.show_all()

        task_button.enable()

    def _on_delete_event(self, widget, event):
        return self.quit()

    def run(self, *args, **kwargs):
        Gtk.main()

    def quit(self, *args, **kwargs):
        if self.session.is_running():
            return self.hide()
        else:
            Gtk.main_quit()

    @on(Events.Session, [State.finished])
    def show(self, *args, **kwargs):
        self.event.send(State.showed)

        logger.debug("view showed")

        self.window.present_with_time(time.time())

    def hide(self, *args, **kwargs):
        self.event.send(State.hid)

        if TrayIcon in self.graph.providers.keys():
            logger.debug("component=view action=hide type=tray")
            return self.window.hide_on_delete()
        else:
            logger.debug("component=view action=hide type=minimize")
            self.window.iconify()
            return Gtk.true

    def show_message(self, message, level):
        self.infobar.show_message(message, level)

    @property
    def widget(self):
        return self.window
