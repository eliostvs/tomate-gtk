import argparse
import locale
import logging
from locale import gettext as _

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gio, Gtk
from wiring.scanning import scan_to_graph

from tomate.pomodoro.app import Application
from tomate.pomodoro.graph import graph

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


def main():
    try:
        options = parse_options()
        setup_logging(options)

        gtk_app = Gtk.Application(application_id=Application.BUS_NAME, flags=Gio.ApplicationFlags.FLAGS_NONE)

        def on_activate(app: Gtk.Application):
            scan_to_graph(["tomate"], graph)
            graph.register_instance("gtk.application", app)

            instance = Application.from_graph(graph)
            instance.Run()

            if instance.IsRunning() and hasattr(app, "notify_startup_complete"):
                app.notify_startup_complete()

        gtk_app.connect("activate", on_activate)
        gtk_app.run()

    except Exception as ex:
        logger.error(ex, exc_info=True)
        raise ex


def setup_logging(options):
    level = logging.DEBUG if options.verbose else logging.INFO
    fmt = "%(levelname)s:%(asctime)s:%(name)s:%(message)s"
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
