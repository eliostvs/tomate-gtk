from __future__ import unicode_literals

import argparse
import locale
import logging
from locale import gettext as _

locale.textdomain('tomate')


def setup_logging(options):
    fmt = '%(levelname)s:%(asctime)s:%(name)s:%(message)s'

    if options.verbose:
        level = logging.DEBUG

    else:
        level = logging.INFO

    logging.basicConfig(level=level, format=fmt)


def parse_options():
    parser = argparse.ArgumentParser(prog='tomate-gtk')

    parser.add_argument(
        "-v", "--verbose",
        default=False,
        action="store_true",
        help=_("Show debug messages")
    )

    return parser.parse_args()


def rounded_percent(percent):
    """
    The icons show 5% steps, so we have to round.
    """
    return percent - percent % 5
