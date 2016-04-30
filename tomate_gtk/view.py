from __future__ import unicode_literals

import logging
import time

from gi.repository import GdkPixbuf, Gtk
from tomate.constant import State
from tomate.event import Subscriber, on, Events
from tomate.view import UI, TrayIcon
from wiring import implements, inject, Module, SingletonScope, Graph

logger = logging.getLogger(__name__)


@implements(UI)
class GtkUI(Subscriber):

    @inject(
        session='tomate.session',
        events='tomate.events',
        config='tomate.config',
        graph=Graph,
        toolbar='view.toolbar',
        timerframe='view.timerframe',
        taskbutton='view.taskbutton',
    )
    def __init__(self, session, events, config, graph, toolbar, timerframe, taskbutton):
        self.config = config
        self.session = session
        self.event = events.View
        self.graph = graph

        self.window = self._build_window(taskbutton, timerframe, toolbar)
        self.window.show_all()

        self.session.change_task()

    def _build_window(self, taskbutton, timerframe, toolbar):
        window = Gtk.Window(
                title='Tomate',
                icon=GdkPixbuf.Pixbuf.new_from_file(self.config.get_icon_path('tomate', 22)),
                window_position=Gtk.WindowPosition.CENTER,
                resizable=False)

        window.set_size_request(350, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(toolbar.widget, False, False, 0)
        box.pack_start(timerframe.widget, True, True, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 8)
        box.pack_start(taskbutton.widget, True, True, 0)

        window.add(box)

        window.connect('delete-event', self._on_window_delete_event)

        return window

    def _on_window_delete_event(self, window, event):
        return self.quit()

    def run(self, *args, **kwargs):
        Gtk.main()

    def quit(self, *args, **kwargs):
        if self.session.timer_is_running():
            return self.hide()

        else:
            Gtk.main_quit()

    @on(Events.Session, [State.finished])
    def show(self, *args, **kwargs):
        logger.debug('View is showing')

        self.event.send(State.showing)

        return self.window.present_with_time(time.time())

    def hide(self, *args, **kwargs):
        logger.debug('View is hiding')

        self.event.send(State.hiding)

        if TrayIcon in self.graph.providers.keys():
            return self.window.hide_on_delete()

        self.window.iconify()

        return Gtk.true

    @property
    def widget(self):
        return self.window


class ViewModule(Module):
    factories = {
        'tomate.view': (GtkUI, SingletonScope)
    }
