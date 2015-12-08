from __future__ import unicode_literals

import logging
import time

from gi.repository import GdkPixbuf, Gtk
from wiring import implements, inject, Module, SingletonScope

from tomate.constant import State
from tomate.event import Subscriber, on, Events
from tomate.view import IView

logger = logging.getLogger(__name__)


@implements(IView)
class GtkView(Subscriber):

    @inject(
        session='tomate.session',
        events='tomate.events',
        config='tomate.config',
        toolbar='view.toolbar',
        timerframe='view.timerframe',
        taskbutton='view.taskbutton',
        infobar='view.infobar',
    )
    def __init__(self, session, events, config, toolbar, timerframe, taskbutton, infobar):
        self.config = config
        self.session = session
        self.event = events.View

        self.window = Gtk.Window(
            title='Tomate',
            icon=GdkPixbuf.Pixbuf.new_from_file(self.config.get_icon_path('tomate', 22)),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False
        )
        self.window.set_size_request(350, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(toolbar.widget, False, False, 0)
        box.pack_start(infobar.widget, False, False, 0)
        box.pack_start(timerframe.widget, True, True, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 8)
        box.pack_start(taskbutton.widget, True, True, 0)

        self.window.connect('delete-event', self.on_window_delete_event)

        self.window.add(box)

        self.window.show_all()

        self.session.change_task()

    def on_window_delete_event(self, window, event):
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

        return self.window.hide_on_delete()

    @property
    def widget(self):
        return self.window


class ViewModule(Module):
    factories = {
        'tomate.view': (GtkView, SingletonScope)
    }
