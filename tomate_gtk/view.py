from __future__ import unicode_literals

import logging
import time

from gi.repository import GdkPixbuf, Gtk
from wiring import implements, inject, Graph, SingletonScope
from wiring.scanning import register
from tomate.constant import State
from tomate.event import Subscriber, on, Events
from tomate.view import UI, TrayIcon

logger = logging.getLogger(__name__)


@register.factory('tomate.view', scope=SingletonScope)
@implements(UI)
class GtkUI(Subscriber):
    @inject(
        session='tomate.session',
        event='tomate.events.view',
        config='tomate.config',
        graph=Graph,
        toolbar='view.toolbar',
        timerframe='view.timerframe',
        taskbutton='view.taskbutton',
        infobar='view.infobar'
    )
    def __init__(self, session, event, config, graph, toolbar, timerframe, taskbutton, infobar):
        self.config = config
        self.session = session
        self.event = event
        self.graph = graph
        self.infobar = infobar.widget

        self.window = Gtk.Window(
            title='Tomate',
            icon=GdkPixbuf.Pixbuf.new_from_file(self.config.get_icon_path('tomate', 22)),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False)

        self.window.set_size_request(350, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(toolbar.widget, False, False, 0)
        box.pack_start(self.infobar, False, False, 0)
        box.pack_start(timerframe.widget, True, True, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 8)
        box.pack_start(taskbutton.widget, True, True, 0)

        self.window.add(box)

        self.window.connect('delete-event', lambda widget, event: self.quit())

        self.window.show_all()

        self.session.change_task()

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

        logger.debug('view showed')

        self.window.present_with_time(time.time())

    def hide(self, *args, **kwargs):
        self.event.send(State.hid)

        logger.debug('view hid')

        if TrayIcon in self.graph.providers.keys():
            return self.window.hide_on_delete()

        self.window.iconify()

        return Gtk.true

    def show_message(self, message, level):
        self.infobar.show_message(message, level)

    @property
    def widget(self):
        return self.window
