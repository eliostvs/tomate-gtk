from __future__ import unicode_literals

import unittest

from mock import patch
from wiring import FactoryProvider, SingletonScope


class TestPlugin(unittest.TestCase):

    @patch('tomate.plugin.Subscriber.disconnect')
    @patch('tomate.plugin.Subscriber.connect')
    def test_interface(self, connect, disconnect):
        from tomate.plugin import Plugin
        from yapsy.IPlugin import IPlugin

        class Dummy(Plugin):
            pass

        dummy = Dummy()

        self.assertIsInstance(dummy, IPlugin)

        dummy.activate()
        connect.assert_called_once_with()

        dummy.deactivate()
        disconnect.assert_called_once_with()


class TestProviderModule(unittest.TestCase):

    def test_module(self):
        from yapsy.PluginManagerDecorator import PluginManagerDecorator
        from tomate.plugin import PluginProvider
        from tomate.graph import graph

        PluginProvider().add_to(graph)

        provider = graph.providers['tomate.plugin']
        self.assertEqual(['tomate.plugin'], graph.providers.keys())

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertEqual(provider.dependencies, {})

        plugin_manager = graph.get('tomate.plugin')
        self.assertIsInstance(plugin_manager, PluginManagerDecorator)
