from __future__ import unicode_literals

import unittest

import six
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.timerframe import TimerFrame, TimerFrameModule


class TestTimerFrame(unittest.TestCase):

    def test_module(self, *args):
        six.assertCountEqual(self, ['view.timerframe'], TimerFrameModule.providers.keys())

        TimerFrameModule().add_to(graph)

        provider = graph.providers['view.timerframe']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({}, provider.dependencies)

        about = graph.get('view.timerframe')
        self.assertIsInstance(about, TimerFrame)
