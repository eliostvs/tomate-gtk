from __future__ import unicode_literals

import logging
import sys

import dbus.mainloop.glib
import gi
import six
from gi.repository import Gdk
from tomate.app import Application
from tomate.graph import graph
from wiring.scanning import scan_to_graph

from .utils import parse_options, setup_logging

gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

logger = logging.getLogger(__name__)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        scan_to_graph(['tomate', 'tomate_gtk'], graph)

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        app = Application.from_graph(graph)

        graph.validate()

        app.run()

        if app.is_running():
            Gdk.notify_startup_complete()

    except Exception as ex:
        logger.error(ex, exc_info=True)

        six.reraise(*sys.exc_info())
