from __future__ import unicode_literals

import logging
import time

from gi.repository import Gtk

from tomate.base import ConnectSignalMixin
from tomate.signals import tomate_signals
from tomate.view import IView

from .widgets import indicator, window

logger = logging.getLogger(__name__)


class GtkView(IView, ConnectSignalMixin):

    signals = (
        ('window_hid', 'hide'),
        ('window_showed', 'show'),
        ('session_ended', 'show_window'),
    )

    def __init__(self):
        self.indicator = indicator.Indicator()

        self.window = window.Window()

        self.connect_signals()

    def run(self):
        logger.debug('window run')

        Gtk.main()

    def quit(self, *args, **kwargs):
        Gtk.main_quit()

        logger.debug('window quit')

    def show(self):
        tomate_signals.emit('window showed')
        return self.present_with_time(time.time())

    def hide(self):
        tomate_signals.emit('window hid')
        return self.hide_on_delete()
