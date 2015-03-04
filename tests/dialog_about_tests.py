from __future__ import unicode_literals

import unittest

from mock import Mock
from wiring import FactoryProvider, SingletonScope

from tomate.config import Config
from tomate.graph import graph


class TestAboutDialog(unittest.TestCase):

    def test_provider_module(self, *args):
        from tomate_gtk.dialogs.about import AboutDialog, AboutDialogProvider

        self.assertEqual(['view.about'], AboutDialogProvider.providers.keys())
        AboutDialogProvider().add_to(graph)

        provider = graph.providers['view.about']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'config': 'tomate.config'}, provider.dependencies)

        graph.register_factory('tomate.signals', Mock)
        graph.register_factory('config.parser', Mock)
        graph.register_factory('tomate.config', Config)

        about = graph.get('view.about')
        self.assertIsInstance(about, AboutDialog)
