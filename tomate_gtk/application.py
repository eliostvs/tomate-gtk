from __future__ import unicode_literals

import logging

import dbus.mainloop.glib
from gi.repository import Gdk
from tomate.application import Application, application_factory
from tomate.signals import ConnectSignalMixin
from tomate.utils import setup_logging

from .utils import parse_options
from .view import GtkView

logger = logging.getLogger(__name__)


class GtkApplication(ConnectSignalMixin,
                     Application):

    view_class = GtkView

    signals = (
        ('app_request', 'on_app_request'),
        ('setting_changed', 'on_setting_changed'),
    )

    def __init__(self, *args, **kwargs):
        super(GtkApplication, self).__init__(*args, **kwargs)

        self.connect_signals()

    def on_app_request(self, *args, **kwargs):
        return self

    def on_setting_changed(self, *args, **kwargs):
        section = kwargs.get('section')

        if section == 'Timer':
            self.change_task(self.pomodoro.task)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        app = application_factory(GtkApplication, options=options)

        app.run()

        if app.is_running():
            Gdk.notify_startup_complete()

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(e, exc_info=True)
        raise e
