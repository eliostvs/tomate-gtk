from __future__ import unicode_literals

import unittest

import dbus
import six
from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.app import AppModule


class TestGtkApp(unittest.TestCase):

    def test_module(self):
        six.assertCountEqual(self, ['tomate.app'], AppModule.providers.keys())

        AppModule().add_to(graph)

        provider = graph.providers['tomate.app']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        dependencies = dict(bus='dbus.session',
                            view='tomate.view',
                            indicator='tomate.indicator',
                            config='tomate.config',
                            plugin='tomate.plugin')

        self.assertDictEqual(provider.dependencies, dependencies)

        graph.register_factory('dbus.session', dbus.SessionBus)
        graph.register_factory('tomate.view', Mock)
        graph.register_factory('tomate.config', Mock)
        graph.register_factory('tomate.plugin', Mock)
        graph.register_factory('tomate.indicator', Mock)
