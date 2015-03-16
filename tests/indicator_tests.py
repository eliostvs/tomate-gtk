from __future__ import unicode_literals

import unittest

from mock import Mock
from tomate.graph import graph
from tomate.tests import SubscriptionMixin
from wiring import FactoryProvider, SingletonScope


class TestIndicator(SubscriptionMixin, unittest.TestCase):

    def setUp(self):
        from tomate_gtk.indicator import IndicatorProvider

        IndicatorProvider().add_to(graph)
        graph.register_instance('tomate.view', Mock())
        graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))

    def create_instance(self):
        return graph.get('tomate.indicator')

    def test_interface_and_provider(self):
        from tomate_gtk.indicator import IIndicator, Indicator, IndicatorProvider

        self.assertEqual(['tomate.indicator'], IndicatorProvider.providers.keys())

        provider = graph.providers['tomate.indicator']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertDictEqual({'config': 'tomate.config', 'view': 'tomate.view'},
                             provider.dependencies)

        indicator = graph.get('tomate.indicator')

        self.assertIsInstance(indicator, Indicator)
        IIndicator.check_compliance(indicator)
