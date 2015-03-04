from __future__ import unicode_literals

import logging
import time

from gi.repository import GdkPixbuf, Gtk
from wiring import implements, inject, Module, SingletonScope

from tomate.view import IView
from tomate.signals import subscribe

logger = logging.getLogger(__name__)


@implements(IView)
class GtkView(Gtk.Window):

    subscriptions = (
        ('setting_changed', 'on_setting_changed'),
    )

    @subscribe
    @inject(session='tomate.session',
            signals='tomate.signals',
            config='tomate.config',
            toolbar='view.toolbar',
            timerframe='view.timerframe',
            taskbutton='view.taskbutton')
    def __init__(self, session, signals, config, toolbar, timerframe, taskbutton):
        self.config = config
        self.session = session
        self.signals = signals

        Gtk.Window.__init__(
            self,
            title='Tomate',
            icon=GdkPixbuf.Pixbuf.new_from_file(
                self.config.get_icon_path('tomate', 22)
            ),
            window_position=Gtk.WindowPosition.CENTER,
            resizable=False
        )
        self.set_size_request(350, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(toolbar, False, False, 0)
        box.pack_start(timerframe, True, True, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL),
                       False, False, 8)
        box.pack_start(taskbutton, True, True, 0)

        self.connect('delete-event', self.on_window_delete_event)

        self.add(box)

        self.show_all()

        self.session.change_task()

    def on_window_delete_event(self, window, event):
        return self.quit()

    def run(self):
        Gtk.main()

    def quit(self):
        if self.session.timer_is_running():
            return self.hide()

        else:
            Gtk.main_quit()

    def show(self):
        logger.debug('view show')
        self.signals.emit('view_showed')
        return self.present_with_time(time.time())

    def hide(self):
        logger.debug('view hide')
        self.signals.emit('view_hid')
        return self.hide_on_delete()

    def on_setting_changed(self, *args, **kwargs):
        if kwargs.get('section') == 'timer':
            self.session.change_task()


class ViewProvider(Module):
    factories = {
        'tomate.view': (GtkView, SingletonScope)
    }
