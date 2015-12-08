from __future__ import unicode_literals

import unittest

import six
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.infobar import InfobarModule, Infobar, InfobarModule


class TestInfobar(unittest.TestCase):

    def setUp(self):
        InfobarModule().add_to(graph)

    def test_module(self, *args):
        six.assertCountEqual(self, ['view.infobar'], InfobarModule.providers.keys())

        provider = graph.providers['view.infobar']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({},  provider.dependencies)

        infobar = graph.get('view.infobar')

        self.assertIsInstance(infobar, Infobar)
