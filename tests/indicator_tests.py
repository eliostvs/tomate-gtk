from __future__ import unicode_literals

import unittest

from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope


class TestIndicator(unittest.TestCase):

    def test_interface_and_provider(self):
        from tomate_gtk.indicator import IIndicator, Indicator, IndicatorProvider

        self.assertEqual(['tomate.indicator'], IndicatorProvider.providers.keys())
        IndicatorProvider().add_to(graph)

        provider = graph.providers['tomate.indicator']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertEqual(provider.dependencies, {'config': 'tomate.config', 'view': 'tomate.view'})

        graph.register_instance('tomate.view', Mock())
        graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))

        indicator = graph.get('tomate.indicator')

        self.assertIsInstance(indicator, Indicator)
        IIndicator.check_compliance(indicator)
