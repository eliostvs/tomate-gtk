from __future__ import unicode_literals

import logging

import dbus.mainloop.glib
from gi.repository import Gdk
from tomate.application import application_factory, Application
from tomate.base import AutoConnectSignalMixin
from tomate.utils import setup_logging

from .utils import parse_options
from .widgets.window import Window

logger = logging.getLogger(__name__)


class GtkApplication(AutoConnectSignalMixin,
                     Application):

    view_class = Window

    signals = (
        ('app_exit', 'exit'),
        ('session_duration_changed', 'on_configuration_changed'),
    )

    def on_configuration_changed(self, sender=None, **kwargs):
        section = kwargs.get('section')
        option = kwargs.get('option')
        value = kwargs.get('value')

        self.profile.set(section, option, value)

        if 'duration' in option:
            self.pomodoro.change_task(self.__class__, task=self.pomodoro.task)

        logger.debug('Configuration %s in section %s changed to %s',
                     option, section, value)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        app = application_factory(GtkApplication, options=options)

        app.start()

        if app.is_running():
            Gdk.notify_startup_complete()

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(e, exc_info=True)
        raise e
