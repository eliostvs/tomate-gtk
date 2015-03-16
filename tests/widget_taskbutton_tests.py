from __future__ import unicode_literals

import unittest

from mock import Mock
from wiring import FactoryProvider, SingletonScope

from tomate.graph import graph
from tomate.tests import SubscriptionMixin


class TestTaskButtonSubscriptions(SubscriptionMixin,
                                  unittest.TestCase):

    def create_instance(self):
        from tomate_gtk.widgets.taskbutton import TaskButton

        return TaskButton(session=Mock())


class TestTaskButton(unittest.TestCase):

    def test_provider_module(self, *args):
        from tomate_gtk.widgets.taskbutton import TaskButton, TaskButtonProvider

        self.assertEqual(['view.taskbutton'], TaskButtonProvider.providers.keys())
        TaskButtonProvider().add_to(graph)

        provider = graph.providers['view.taskbutton']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'session': 'tomate.session'}, provider.dependencies)

        graph.register_factory('tomate.session', Mock)

        taskbutton = graph.get('view.taskbutton')
        self.assertIsInstance(taskbutton, TaskButton)
