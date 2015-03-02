from __future__ import unicode_literals

import unittest

from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope


class TestAboutDialog(unittest.TestCase):

    def test_provider_module(self, *args):
        from tomate_gtk.widgets.toolbar import Toolbar, ToolbarProvider
        from tomate_gtk.widgets.appmenu import Appmenu

        self.assertEqual(['view.toolbar'], ToolbarProvider.providers.keys())
        ToolbarProvider().add_to(graph)

        provider = graph.providers['view.toolbar']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'session': 'tomate.session', 'appmenu': 'view.appmenu'},
                             provider.dependencies)

        graph.register_factory('view.preference', Mock)
        graph.register_factory('view.about', Mock)
        graph.register_factory('tomate.session', Mock)
        graph.register_factory('tomate.appmenu', Appmenu)

        toolbar = graph.get('view.toolbar')
        self.assertIsInstance(toolbar, Toolbar)
