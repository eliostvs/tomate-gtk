from __future__ import unicode_literals

import unittest

import six
from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.appmenu import Appmenu
from tomate_gtk.widgets.toolbar import Toolbar, ToolbarModule


class TestToolbar(unittest.TestCase):
    def setUp(self):
        graph.register_factory('view.preference', Mock)
        graph.register_factory('view.about', Mock)
        graph.register_factory('tomate.session', Mock)
        graph.register_factory('tomate.appmenu', Appmenu)
        ToolbarModule().add_to(graph)

    def test_module(self):
        six.assertCountEqual(self, ['view.toolbar'], ToolbarModule.providers.keys())

        provider = graph.providers['view.toolbar']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'session': 'tomate.session', 'appmenu': 'view.appmenu'},
                             provider.dependencies)

        toolbar = graph.get('view.toolbar')

        self.assertIsInstance(toolbar, Toolbar)
