from __future__ import unicode_literals

import unittest

import six
from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope, Graph

from tomate_gtk.widgets.appmenu import Appmenu, AppmenuModule

class TestAppmenu(unittest.TestCase):

    def test_module(self, *args):
        six.assertCountEqual(self, ['view.appmenu'], AppmenuModule.providers.keys())

        AppmenuModule().add_to(graph)

        provider = graph.providers['view.appmenu']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'about': 'view.about', 'preference': 'view.preference', 'graph': Graph},
                             provider.dependencies)

        graph.register_factory('view.preference', Mock)
        graph.register_factory('view.about', Mock)

        appmenu = graph.get('view.appmenu')

        self.assertIsInstance(appmenu, Appmenu)
