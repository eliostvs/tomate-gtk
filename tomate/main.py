import argparse
import locale
import logging
from locale import gettext as _

import dbus.mainloop.glib
import gi
from wiring.scanning import scan_to_graph

from tomate.core.app import Application
from tomate.core.graph import graph

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        scan_to_graph(["tomate"], graph)

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

        app = Application.from_graph(graph)

        app.run()

        if app.is_running():
            Gdk.notify_startup_complete()

    except Exception as ex:
        logger.error(ex, exc_info=True)

        raise ex


def setup_logging(options):
    fmt = "%(levelname)s:%(asctime)s:%(name)s:%(message)s"

    if options.verbose:
        level = logging.DEBUG

    else:
        level = logging.INFO

    logging.basicConfig(level=level, format=fmt)


def parse_options():
    parser = argparse.ArgumentParser(prog="tomate-gtk")

    parser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help=_("Show debug messages"),
    )

    return parser.parse_args()
