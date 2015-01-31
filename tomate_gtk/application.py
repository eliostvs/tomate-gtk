from __future__ import unicode_literals

import logging

import dbus.mainloop.glib
from gi.repository import Gdk
from tomate.application import Application, application_factory
from tomate.base import AutoConnectSignalMixin
from tomate.utils import setup_logging

from .utils import parse_options
from .view import GtkView

logger = logging.getLogger(__name__)


class GtkApplication(AutoConnectSignalMixin,
                     Application):

    bus_name = 'com.github.TomateGtk'
    bus_object_path = '/'
    bus_interface_name = 'com.github.TomateGtk'

    view_class = GtkView

    signals = (
        ('app_quit', 'quit'),
        ('setting_changed', 'on_setting_changed'),
    )

    def on_setting_changed(self, sender=None, **kwargs):
        section = kwargs.get('section')
        option = kwargs.get('option')
        value = kwargs.get('value')

        self.profile.set(section, option, value)

        if 'duration' in option:
            self.pomodoro.change_task(task=self.pomodoro.task)

        logger.debug('Configuration %s in section %s changed to %s',
                     option, section, value)


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
