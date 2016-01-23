from __future__ import unicode_literals

import unittest

import six
from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.dialogs.preference import (ExtensionStack, PreferenceDialog,
                                           PreferenceDialogModule,
                                           TimerDurationStack)


class TestAboutDialog(unittest.TestCase):

    def test_module(self, *args):
        providers = [
            'view.preference',
            'view.preference.extension',
            'view.preference.duration',
        ]

        six.assertCountEqual(self, providers, PreferenceDialogModule.providers.keys())

        PreferenceDialogModule().add_to(graph)

        # Extension Stack
        provider = graph.providers['view.preference.extension']
        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertDictEqual({'config': 'tomate.config', 'plugin': 'tomate.plugin'},
                             provider.dependencies)

        # Duration Stack
        provider = graph.providers['view.preference.duration']
        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertDictEqual({'config': 'tomate.config'}, provider.dependencies)

        # Preference Dialog
        provider = graph.providers['view.preference']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'extension': 'view.preference.extension',
                              'duration': 'view.preference.duration'},
                             provider.dependencies)

        config = Mock(**{'get_int.return_value': 25})
        graph.register_instance('tomate.config', config)
        graph.register_factory('tomate.plugin', Mock)
        graph.register_factory('view.preference.extension', ExtensionStack)
        graph.register_factory('view.preference.duration', TimerDurationStack)

        preference = graph.get('view.preference')
        self.assertIsInstance(preference, PreferenceDialog)
