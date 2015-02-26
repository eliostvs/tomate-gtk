from __future__ import unicode_literals

# import logging

# import dbus.mainloop.glib
# from gi.repository import Gdk
# from tomate.application import application_factory

# from .utils import parse_options, setup_logging
# from .view import GtkView

# logger = logging.getLogger(__name__)


# def main():
#     try:
#         options = parse_options()
#         setup_logging(options)

#         dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

#         app = application_factory(GtkApplication, GtkView, options=options)

#         app.run()

#         if app.is_running():
#             Gdk.notify_startup_complete()

#     except Exception as e:
#         logger = logging.getLogger(__name__)
#         logger.error(e, exc_info=True)
#         raise e
