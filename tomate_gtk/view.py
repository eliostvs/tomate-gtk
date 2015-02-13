from __future__ import unicode_literals

import logging
import time

from gi.repository import Gtk

from tomate.mixins import ConnectSignalMixin
from tomate.signals import tomate_signals
from tomate.interfaces import IView

from .widgets import indicator, window

logger = logging.getLogger(__name__)


class GtkView(IView, ConnectSignalMixin):

    signals = (
        ('session_ended', 'show'),
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
        return True

    def show(self, *args, **kwargs):
        tomate_signals.emit('window_showed')
        return self.window.present_with_time(time.time())

    def hide(self, *args, **kwargs):
        tomate_signals.emit('window_hid')
        return self.window.hide_on_delete()
