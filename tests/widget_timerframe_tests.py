from __future__ import unicode_literals

import unittest

from wiring import FactoryProvider, SingletonScope

from tomate.graph import graph


class TestAboutDialog(unittest.TestCase):

    def test_provider_module(self, *args):
        from tomate_gtk.widgets.timerframe import TimerFrame, TimerFrameProvider

        self.assertEqual(['view.timerframe'], TimerFrameProvider.providers.keys())
        TimerFrameProvider().add_to(graph)

        provider = graph.providers['view.timerframe']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        self.assertDictEqual({}, provider.dependencies)

        about = graph.get('view.timerframe')
        self.assertIsInstance(about, TimerFrame)
