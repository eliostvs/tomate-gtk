from __future__ import unicode_literals

import unittest

from mock import Mock
from wiring import FactoryProvider, Graph, SingletonScope

from tomate.enums import State, Task


class TestSessionInterface(unittest.TestCase):

    def test_interface(self):
        from tomate.session import ISession, Session

        session = Session(timer=Mock(),
                          config=Mock(**{'get_int.return_value': 25}),
                          signals=Mock())
        ISession.check_compliance(session)


class TestSession(unittest.TestCase):

    def setUp(self):
        from tomate.session import Session

        self.session = Session(timer=Mock(),
                               config=Mock(**{'get_int.return_value': 25}),
                               signals=Mock())

    def test_default_state(self):
        self.assertEqual(Task.pomodoro, self.session.task)
        self.assertEqual(0, self.session.count)

    def test_session_start(self):
        self.session.state = State.running
        self.assertFalse(self.session.start())

        self.session.state = State.stopped
        self.assertTrue(self.session.start())
        self.assertEqual(State.running, self.session.state)

    def test_session_interrupt(self):
        self.session.state = State.stopped
        self.assertFalse(self.session.interrupt())

        self.session.state = State.running
        self.session.timer.state = State.running
        self.assertTrue(self.session.interrupt())
        self.assertEqual(State.stopped, self.session.state)

    def test_session_reset(self):
        self.session.state = State.running
        self.session.count = 10

        self.assertFalse(self.session.reset())

        self.session.state = State.stopped

        self.assertTrue(self.session.reset())
        self.assertEqual(0, self.session.count)

    def test_session_end(self):
        self.session.config.get_int.return_value = 4
        self.session.state = State.stopped
        self.session.count = 0

        self.assertFalse(self.session.end())

        self.session.state = State.running
        self.session.timer.state = State.stopped

        self.assertTrue(self.session.end())
        self.assertEqual(State.stopped, self.session.state)
        self.assertEqual(1, self.session.count)
        self.assertEqual(Task.shortbreak, self.session.task)

        self.session.state = State.running
        self.session.task = Task.pomodoro
        self.session.count = 3

        self.assertTrue(self.session.end())
        self.assertEqual(Task.longbreak, self.session.task)

        self.session.state = State.running
        self.session.task = Task.shortbreak

        self.assertTrue(self.session.end())
        self.assertEqual(Task.pomodoro, self.session.task)

    def test_session_status(self):
        self.session.count = 2
        self.session.task = Task.shortbreak
        self.session.state = State.running
        self.session.config.get_int.return_value = 5

        status = dict(task=Task.shortbreak,
                      sessions=2,
                      state=State.running,
                      time_left=5 * 60)

        self.assertEqual(status, self.session.status())

    def test_session_duration(self):
        self.assertEqual(25 * 60, self.session.duration)
        self.session.config.get_int.assert_called_once_with('Timer', 'pomodoro_duration')

    def test_change_task(self):
        self.session.state = State.running
        self.assertEqual(None, self.session.change_task())

        self.session.state = State.stopped
        self.assertTrue(self.session.change_task(task=Task.shortbreak))
        self.assertEqual(Task.shortbreak, self.session.task)


class TestSessionSignals(unittest.TestCase):

    def setUp(self, *args):
        from tomate.session import Session

        self.session = Session(timer=Mock(),
                               config=Mock(**{'get_int.return_value': 25}),
                               signals=Mock())

    def test_should_emit_session_started(self):
        self.session.start()

        self.session.signals.emit.assert_called_once_with('session_started',
                                                          task=Task.pomodoro,
                                                          sessions=0,
                                                          state=State.running,
                                                          time_left=1500)

    def test_should_emit_session_interrupt(self):
        self.session.state = State.running
        self.session.timer.state = State.running
        self.session.interrupt()

        self.session.signals.emit.assert_called_once_with('session_interrupted',
                                                          task=Task.pomodoro,
                                                          sessions=0,
                                                          state=State.stopped,
                                                          time_left=1500)

    def test_should_emit_session_reseted(self):
        self.session.count = 2
        self.session.reset()

        self.session.signals.emit.assert_called_once_with('sessions_reseted',
                                                          task=Task.pomodoro,
                                                          sessions=0,
                                                          state=State.stopped,
                                                          time_left=1500)

    def test_should_emit_session_end(self):
        self.session.state = State.running
        self.session.timer.State = State.stopped
        self.session.config.get_int.return_value = 5
        self.session.end()

        self.session.signals.emit.assert_called_once_with('session_ended',
                                                          task=Task.shortbreak,
                                                          sessions=1,
                                                          state=State.stopped,
                                                          time_left=300)

    def test_should_emit_task_changed(self):
        self.session.config.get_int.return_value = 15
        self.session.change_task(task=Task.longbreak)

        self.session.signals.emit.assert_called_once_with('task_changed',
                                                          task=Task.longbreak,
                                                          sessions=0,
                                                          state=State.stopped,
                                                          time_left=900)

        self.session.signals.reset_mock()
        self.session.change_task()

        self.session.signals.emit.assert_called_once_with('task_changed',
                                                          task=Task.longbreak,
                                                          sessions=0,
                                                          state=State.stopped,
                                                          time_left=900)


class TestSessionModule(unittest.TestCase):

    def test_module(self):
        from tomate.session import Session, SessionProvider

        graph = Graph()

        self.assertEqual(['tomate.session'], SessionProvider.providers.keys())
        SessionProvider().add_to(graph)

        provider = graph.providers['tomate.session']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertEqual(provider.dependencies,
                         dict(signals='tomate.signals',
                              config='tomate.config',
                              timer='tomate.timer'))

        graph.register_instance('tomate.signals', Mock())
        graph.register_instance('tomate.timer', Mock())
        graph.register_instance('tomate.config', Mock())
        self.assertIsInstance(graph.get('tomate.session'), Session)
