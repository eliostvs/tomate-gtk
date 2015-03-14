from __future__ import unicode_literals

import unittest

import dbus
from mock import Mock, patch
from tomate.app import IApplication
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope


class TestGtkApp(unittest.TestCase):

    def test_inteface_and_module_provider(self):
        from tomate_gtk.app import GtkApplication, AppProvider

        self.assertEqual(['tomate.app'], AppProvider.providers.keys())
        AppProvider().add_to(graph)

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

        with patch('tomate.app.dbus'):
            app = graph.get('tomate.app')

            self.assertIsInstance(app, GtkApplication)
            IApplication.check_compliance(app)
