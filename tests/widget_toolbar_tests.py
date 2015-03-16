from __future__ import unicode_literals

import unittest

from mock import Mock
from wiring import FactoryProvider, SingletonScope

from tomate.graph import graph
from tomate.tests import SubscriptionMixin


class TestToolbar(SubscriptionMixin, unittest.TestCase):

    def setUp(self):
        from tomate_gtk.widgets.toolbar import ToolbarProvider
        from tomate_gtk.widgets.appmenu import Appmenu

        graph.register_factory('view.preference', Mock)
        graph.register_factory('view.about', Mock)
        graph.register_factory('tomate.session', Mock)
        graph.register_factory('tomate.appmenu', Appmenu)

        ToolbarProvider().add_to(graph)

    def create_instance(self):
        return graph.get('view.toolbar')

    def test_provider_module(self, *args):
        from tomate_gtk.widgets.toolbar import Toolbar, ToolbarProvider

        self.assertEqual(['view.toolbar'], ToolbarProvider.providers.keys())

        provider = graph.providers['view.toolbar']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'session': 'tomate.session', 'appmenu': 'view.appmenu'},
                             provider.dependencies)

        toolbar = graph.get('view.toolbar')
        self.assertIsInstance(toolbar, Toolbar)
