from __future__ import unicode_literals

import logging

import dbus.mainloop.glib
from gi.repository import Gdk

from tomate.app import application_factory
from tomate.config import ConfigProvider
from tomate.graph import graph
from tomate.plugin import PluginProvider
from tomate.session import SessionProvider
from tomate.signals import SignalsProvider
from tomate.timer import TimerProvider

from .app import AppProvider
from .dialogs import AboutDialogProvider, PreferenceDialogProvider
from .indicator import IndicatorProvider
from .utils import parse_options, setup_logging
from .view import ViewProvider
from .widgets import (AppmenuProvider, TaskButtonProvider, TimerFrameProvider,
                      ToolbarProvider)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        # Base
        PluginProvider().add_to(graph)
        SignalsProvider().add_to(graph)
        ConfigProvider().add_to(graph)
        TimerProvider().add_to(graph)
        SessionProvider().add_to(graph)

        # Dialogs
        AboutDialogProvider().add_to(graph)
        PreferenceDialogProvider().add_to(graph)

        # Main window
        AppmenuProvider().add_to(graph)
        ToolbarProvider().add_to(graph)
        TimerFrameProvider().add_to(graph)
        TaskButtonProvider().add_to(graph)
        ViewProvider().add_to(graph)
        IndicatorProvider().add_to(graph)

        # App
        AppProvider().add_to(graph)

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        app = application_factory(graph)

        app.run()

        if app.is_running():
            Gdk.notify_startup_complete()

    except Exception as err:
        logger = logging.getLogger(__name__)
        logger.error(err, exc_info=True)
        raise err
