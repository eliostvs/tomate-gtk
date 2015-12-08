from __future__ import unicode_literals

import unittest

import six
from mock import Mock
from tomate.config import Config
from tomate.graph import graph
from tomate.view import IView
from wiring import FactoryProvider, SingletonScope


class TestGtkView(unittest.TestCase):

    def setUp(self):
        from tomate_gtk.view import ViewModule
        from tomate_gtk.widgets.taskbutton import TaskButton
        from tomate_gtk.widgets.timerframe import TimerFrame
        from tomate_gtk.widgets.toolbar import Toolbar
        from tomate_gtk.widgets.appmenu import Appmenu
        from tomate_gtk.widgets.infobar import Infobar

        ViewModule().add_to(graph)

        graph.register_factory('tomate.events', Mock)
        graph.register_factory('tomate.session', Mock)
        graph.register_factory('config.parser', Mock)
        graph.register_factory('tomate.config', Config)
        graph.register_factory('view.about', Mock)
        graph.register_factory('view.preference', Mock)
        graph.register_factory('view.appmenu', Appmenu)
        graph.register_factory('view.toolbar', Toolbar)
        graph.register_factory('view.timerframe', TimerFrame)
        graph.register_factory('view.taskbutton', TaskButton)
        graph.register_factory('view.infobar', Infobar)

    def test_module(self, *args):
        from tomate_gtk.view import GtkView, ViewModule

        six.assertCountEqual(self, ['tomate.view'], ViewModule.providers.keys())

        provider = graph.providers['tomate.view']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        dependencies = dict(session='tomate.session',
                            events='tomate.events',
                            config='tomate.config',
                            toolbar='view.toolbar',
                            timerframe='view.timerframe',
                            taskbutton='view.taskbutton',
                            infobar='view.infobar')

        self.assertDictEqual(dependencies, provider.dependencies)

        view = graph.get('tomate.view')
        self.assertIsInstance(view, GtkView)

    def test_interface(self):
        view = graph.get('tomate.view')

        IView.check_compliance(view)
