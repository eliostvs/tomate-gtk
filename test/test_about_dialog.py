from __future__ import unicode_literals

import unittest

import six
from mock import Mock
from tomate.config import Config
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.dialogs.about import AboutDialog, AboutDialogModule


class TestAboutDialog(unittest.TestCase):

    def test_module(self, *args):
        six.assertCountEqual(self, ['view.about'], AboutDialogModule.providers.keys())

        AboutDialogModule().add_to(graph)

        provider = graph.providers['view.about']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'config': 'tomate.config'}, provider.dependencies)

        graph.register_factory('tomate.events', Mock)
        graph.register_factory('config.parser', Mock)
        graph.register_factory('tomate.config', Config)

        about = graph.get('view.about')

        self.assertIsInstance(about, AboutDialog)
