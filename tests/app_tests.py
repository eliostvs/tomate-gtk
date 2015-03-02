from __future__ import unicode_literals

import unittest

from mock import Mock
from tomate.app import IApplication


class TestGtkApp(unittest.TestCase):

    def test_inteface(self):
        from tomate_gtk.app import GtkApplication

        app = GtkApplication(bus=Mock(),
                             view=Mock(),
                             indicator=Mock(),
                             config=Mock(),
                             plugin=Mock())

        IApplication.check_compliance(app)
