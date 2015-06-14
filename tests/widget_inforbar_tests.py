from __future__ import unicode_literals

import unittest

from wiring import FactoryProvider, SingletonScope

from tomate.graph import graph

from tomate_gtk.widgets.infobar import InfobarProvider, IInfobar, Infobar


class TestInfobar(unittest.TestCase):

    def setUp(self):

        InfobarProvider().add_to(graph)

    def create_instance(self):
        return graph.get('view.infobarr')

    def test_provider_module(self, *args):
        self.assertEqual(['view.infobar'], InfobarProvider.providers.keys())

        provider = graph.providers['view.infobar']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({},  provider.dependencies)

        infobar = graph.get('view.infobar')
        self.assertIsInstance(infobar, Infobar)

        IInfobar.check_compliance(infobar)
