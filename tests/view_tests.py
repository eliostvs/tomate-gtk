from __future__ import unicode_literals

import unittest

from mock import Mock
from wiring import FactoryProvider, SingletonScope

from tomate.config import Config
from tomate.graph import graph
from tomate.tests import SubscriptionMixin
from tomate.view import IView


class TestGtkView(SubscriptionMixin, unittest.TestCase):

    def setUp(self):
        from tomate_gtk.view import ViewProvider
        from tomate_gtk.widgets.taskbutton import TaskButton
        from tomate_gtk.widgets.timerframe import TimerFrame
        from tomate_gtk.widgets.toolbar import Toolbar
        from tomate_gtk.widgets.appmenu import Appmenu

        ViewProvider().add_to(graph)

        graph.register_factory('tomate.signals', Mock)
        graph.register_factory('tomate.session', Mock)
        graph.register_factory('config.parser', Mock)
        graph.register_factory('tomate.config', Config)
        graph.register_factory('view.about', Mock)
        graph.register_factory('view.preference', Mock)
        graph.register_factory('view.appmenu', Appmenu)
        graph.register_factory('view.toolbar', Toolbar)
        graph.register_factory('view.timerframe', TimerFrame)
        graph.register_factory('view.taskbutton', TaskButton)

    def create_instance(self):
        return graph.get('tomate.view')

    def test_interface_and_module_provider(self, *args):
        from tomate_gtk.view import GtkView, ViewProvider

        self.assertEqual(['tomate.view'], ViewProvider.providers.keys())

        provider = graph.providers['tomate.view']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        dependencies = dict(session='tomate.session',
                            signals='tomate.signals',
                            config='tomate.config',
                            toolbar='view.toolbar',
                            timerframe='view.timerframe',
                            taskbutton='view.taskbutton')

        self.assertDictEqual(dependencies, provider.dependencies)

        view = graph.get('tomate.view')
        self.assertIsInstance(view, GtkView)
        IView.check_compliance(view)
