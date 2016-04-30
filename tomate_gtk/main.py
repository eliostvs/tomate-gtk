from __future__ import unicode_literals

import logging
import sys

import dbus.mainloop.glib
import gi
import six

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import Gdk

from tomate.app import Application, ApplicationModule
from tomate.config import ConfigModule
from tomate.event import EventModule
from tomate.graph import graph
from tomate.plugin import PluginModule
from tomate.session import SessionModule
from tomate.timer import TimerModule
from tomate.proxy import ProxyModule
from .dialogs import AboutDialogModule, PreferenceDialogModule
from .utils import parse_options, setup_logging
from .view import ViewModule
from .widgets import (AppmenuModule, TaskButtonModule, TimerFrameModule,
                      ToolbarModule, MenuModule)

logger = logging.getLogger(__name__)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        # Base
        ProxyModule().add_to(graph)
        PluginModule().add_to(graph)
        EventModule().add_to(graph)
        ConfigModule().add_to(graph)
        TimerModule().add_to(graph)
        SessionModule().add_to(graph)

        # Dialogs
        AboutDialogModule().add_to(graph)
        PreferenceDialogModule().add_to(graph)

        # Main window
        AppmenuModule().add_to(graph)
        ToolbarModule().add_to(graph)
        TimerFrameModule().add_to(graph)
        TaskButtonModule().add_to(graph)
        MenuModule().add_to(graph)
        ViewModule().add_to(graph)

        # App
        ApplicationModule().add_to(graph)

        graph.validate()

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        app = Application.from_graph(graph)

        app.run()

        if app.is_running():
            Gdk.notify_startup_complete()

    except Exception as ex:
        logger.error(ex, exc_info=True)

        six.reraise(*sys.exc_info())
