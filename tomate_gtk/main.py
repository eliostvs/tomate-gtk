from __future__ import unicode_literals

import logging

import dbus.mainloop.glib
from gi.repository import Gdk

from tomate.config import ConfigModule
from tomate.graph import graph
from tomate.plugin import PluginModule
from tomate.session import SessionModule
from tomate.event import EventsModule
from tomate.timer import TimerModule

from .app import AppModule, GtkApplication
from .dialogs import AboutDialogModule, PreferenceDialogModule
from .indicator import IndicatorModule
from .utils import parse_options, setup_logging
from .view import ViewModule
from .widgets import (AppmenuModule, TaskButtonModule, TimerFrameModule,
                      ToolbarModule, InfobarModule)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        # Base
        PluginModule().add_to(graph)
        EventsModule().add_to(graph)
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
        InfobarModule().add_to(graph)
        ViewModule().add_to(graph)
        IndicatorModule().add_to(graph)

        # App
        AppModule().add_to(graph)

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        app = GtkApplication.from_graph(graph)

        app.run()

        if app.is_running():
            Gdk.notify_startup_complete()

    except Exception as err:
        logger = logging.getLogger(__name__)
        logger.error(err, exc_info=True)
        raise err
