from __future__ import unicode_literals

import unittest

import six
from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.indicator import IIndicator, Indicator, IndicatorModule


class IndicatorTest(unittest.TestCase):

    def setUp(self):
        IndicatorModule().add_to(graph)
        graph.register_instance('tomate.view', Mock())
        graph.register_instance('tomate.config', Mock(**{'get_icon_paths.return_value': ['']}))

    def test_module(self):
        six.assertCountEqual(self, ['tomate.indicator'], IndicatorModule.providers.keys())

        provider = graph.providers['tomate.indicator']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertDictEqual({'config': 'tomate.config', 'view': 'tomate.view'},
                             provider.dependencies)

        indicator = graph.get('tomate.indicator')

        self.assertIsInstance(indicator, Indicator)

    def test_indicator_interface(self):
        indicator = graph.get('tomate.indicator')

        IIndicator.check_compliance(indicator)
