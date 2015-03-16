from __future__ import division, unicode_literals

import unittest

from mock import Mock
from tomate.enums import State
from wiring import FactoryProvider, SingletonScope


class TestTimerInterface(unittest.TestCase):

    def test_interface(self):
        from tomate.timer import ITimer, Timer

        timer = Timer(signals=Mock())
        ITimer.check_compliance(timer)


class TestTimer(unittest.TestCase):

    def setUp(self):
        from tomate.timer import Timer

        self.timer = Timer(signals=Mock())

    def test_init(self):
        self.assertEqual(State.stopped, self.timer.state)
        self.assertEqual(0, self.timer.time_ratio)
        self.assertEqual(0, self.timer.time_left)

    def test_stop(self):
        self.assertFalse(self.timer.stop())

        self.timer.state = State.running

        self.assertTrue(self.timer.stop())
        self.assertEqual(State.stopped, self.timer.state)

    def test_start(self):
        self.timer.state = State.running
        self.assertFalse(self.timer.start(1))

        self.timer.state = State.stopped
        self.assertTrue(self.timer.start(1))
        self.assertEqual(1, self.timer.time_left)
        self.assertEqual(1, self.timer._Timer__seconds)

    def test_timer_ratio(self):
        self.assertEqual(0, self.timer.time_ratio)

        self.timer.start(10)
        self.assertEqual(0, self.timer.time_ratio)

        self.timer.update()
        self.assertEqual(0.1, self.timer.time_ratio)

        self.timer.update()
        self.timer.update()
        self.assertEqual(0.3, self.timer.time_ratio)

    def test_update(self):
        self.assertFalse(False, self.timer.update())

        self.timer.start(2)
        self.assertTrue(self.timer.update())
        self.assertEqual(1, self.timer.time_left)

        self.timer.update()

        self.assertFalse(self.timer.update())
        self.assertEqual(0, self.timer.time_left)
        self.assertEqual(State.stopped, self.timer.state)


class TestTimerSignals(unittest.TestCase):

    def setUp(self):
        from tomate.timer import Timer

        self.timer = Timer(signals=Mock())

    def test_should_emit_time_finished_signal(self):
        self.timer.start(1)
        self.timer.update()
        self.timer.update()

        self.timer.signals.emit.assert_called('timer_finished', time_left=0, time_ratio=0)

    def test_should_emit_time_updated_signal(self):
        self.timer.start(10)
        self.timer.update()

        self.timer.signals.emit.assert_called_once_with('timer_updated', time_left=9, time_ratio=0.1)


class TestTimerProvider(unittest.TestCase):

    def test_module(self):
        from tomate.timer import TimerProvider, Timer
        from tomate.graph import graph

        self.assertEqual(['tomate.timer'], TimerProvider.providers.keys())
        TimerProvider().add_to(graph)

        provider = graph.providers['tomate.timer']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertEqual(provider.dependencies, {'signals': 'tomate.signals'})

        graph.register_instance('tomate.signals', Mock())
        self.assertIsInstance(graph.get('tomate.timer'), Timer)
