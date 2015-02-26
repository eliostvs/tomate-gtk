from __future__ import unicode_literals

import time

from gi.repository import Gtk
from wiring import implements, inject

from tomate.signals import subscribe
from tomate.view import IView


@implements(IView)
class GtkView(object):

    subscriptions = (
        ('session_ended', 'show'),
    )

    @subscribe
    @inject(window='view.window',
            session='tomate.session',
            signals='tomate.signals')
    def __init__(self, session=None, signals=None, window=None):
        self.session = session
        self.signals = signals
        self.window = window

    def run(self):
        Gtk.main()

    def quit(self):
        if self.session.timer_is_running():
            self.hide()

        else:
            Gtk.main_quit()

    def show(self):
        self.signals.emit('window_showed')
        return self.window.present_with_time(time.time())

    def hide(self):
        self.signals.emit('window_hid')
        return self.window.hide_on_delete()
