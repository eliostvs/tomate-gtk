from __future__ import unicode_literals

import argparse
import locale
from locale import gettext as _

locale.textdomain('tomate')


def parse_options():
    parser = argparse.ArgumentParser(prog='tomate-gtk')

    parser.add_argument(
        "-v", "--verbose",
        default=False,
        action="store_true",
        help=_("Show debug messages")
    )

    return parser.parse_args()
