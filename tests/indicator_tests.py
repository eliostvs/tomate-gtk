from __future__ import unicode_literals

import unittest

from mock import Mock
from wiring import FactoryProvider, SingletonScope


class TestIndicatorInterface(unittest.TestCase):

    def test_interface(self):
        from tomate_gtk.indicator import IIndicator, Indicator

        indicator = Indicator(config=Mock(**{'get_icon_paths.return_value': ['']}))
        IIndicator.check_compliance(indicator)


class TestIndicatorProvider(unittest.TestCase):

    def test_provider_module(self):
        from tomate_gtk.indicator import IndicatorProvider, Indicator
        from tomate.graph import graph

        self.assertEqual(['view.indicator'], IndicatorProvider.providers.keys())
        IndicatorProvider().add_to(graph)

        provider = graph.providers['view.indicator']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertEqual(provider.dependencies, {'config': 'tomate.config', 'view': 'tomate.view'})

        graph.register_instance('tomate.view', Mock())
        graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))
        self.assertIsInstance(graph.get('view.indicator'), Indicator)
