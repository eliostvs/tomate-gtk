from __future__ import unicode_literals

import unittest

from mock import Mock


class TestIndicatorInterface(unittest.TestCase):

    def test_interface(self):
        from tomate_gtk.indicator import IIndicator, Indicator

        indicator = Indicator(config=Mock(**{'get_icon_paths.return_value': ['']}))
        IIndicator.check_compliance(indicator)
