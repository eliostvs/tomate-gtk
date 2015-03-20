from __future__ import unicode_literals

import unittest

from mock import Mock
from wiring import FactoryProvider, SingletonScope

from tomate.graph import graph


class TestAppmenu(unittest.TestCase):

    def test_provider_module(self, *args):
        from tomate_gtk.widgets.appmenu import Appmenu, AppmenuProvider

        self.assertEqual(['view.appmenu'], AppmenuProvider.providers.keys())
        AppmenuProvider().add_to(graph)

        provider = graph.providers['view.appmenu']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'about': 'view.about', 'preference': 'view.preference'},
                             provider.dependencies)

        graph.register_factory('view.preference', Mock)
        graph.register_factory('view.about', Mock)

        appmenu = graph.get('view.appmenu')
        self.assertIsInstance(appmenu, Appmenu)
