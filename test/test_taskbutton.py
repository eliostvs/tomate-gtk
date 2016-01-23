from __future__ import unicode_literals

import unittest

from mock import Mock
import six
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.taskbutton import TaskButton, TaskButtonModule


class TestTaskButton(unittest.TestCase):

    def test_module(self):
        six.assertCountEqual(self, ['view.taskbutton'], TaskButtonModule.providers.keys())

        TaskButtonModule().add_to(graph)

        provider = graph.providers['view.taskbutton']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({'session': 'tomate.session'}, provider.dependencies)

        graph.register_factory('tomate.session', Mock)

        taskbutton = graph.get('view.taskbutton')

        self.assertIsInstance(taskbutton, TaskButton)
