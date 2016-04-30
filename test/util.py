from __future__ import unicode_literals

import time

from gi.repository import Gtk


def refresh_gui(delay=0):
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    time.sleep(delay)
