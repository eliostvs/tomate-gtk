from __future__ import unicode_literals

import unittest

from mock import patch
from wiring import Graph, InstanceProvider


class TestConnectSignalMixin(unittest.TestCase):

    def make_dummy(self):
        from tomate.signals import Subscriber

        class Dummy(Subscriber):
            subscriptions = (
                ('updated_timer', 'foo'),
            )

            def foo(self):
                pass

        return Dummy()

    @patch('tomate.signals.TomateNamespace.connect')
    def test_connect_signal(self, mconnect):
        dummy = self.make_dummy()
        dummy.connect()

        mconnect.assert_called_once_with('updated_timer', dummy.foo)

    @patch('tomate.signals.TomateNamespace.disconnect')
    def test_disconnect_signal(self, mdisconnect):
        dummy = self.make_dummy()
        dummy.disconnect()

        mdisconnect.assert_called_once_with('updated_timer', dummy.foo)


@patch('blinker.base.NamedSignal')
class TestTomateNamespace(unittest.TestCase):

    def make_namespace(self):
        from tomate.signals import TomateNamespace

        namespace = TomateNamespace()
        namespace.signal('test')

        return namespace

    def test_emit_signal(self, mNamedSignal):
        namespace = self.make_namespace()

        mNamedSignal.assert_called_once_with('test', None)

        namespace.emit('test', a=1)

        mNamedSignal.return_value.send.assert_called_once_with(a=1)

    def test_connect_signal(self, mNamedSignal):
        namespace = self.make_namespace()

        def function():
            pass

        namespace.connect('test', function)

        mNamedSignal.return_value.connect.assert_called_once_with(function, weak=True)

    def test_disconnect_signal(self, mNamedSignal):
        namespace = self.make_namespace()

        def function():
            pass

        namespace.disconnect('test', function)

        mNamedSignal.return_value.disconnect.assert_called_once_with(function)


class TestSignalProviders(unittest.TestCase):

    def test_module(self):
        from tomate.signals import SignalsProvider, TomateNamespace

        graph = Graph()

        self.assertEqual(['tomate.signals'], SignalsProvider.providers.keys())
        SignalsProvider().add_to(graph)

        provider = graph.providers['tomate.signals']

        self.assertIsInstance(provider, InstanceProvider)
        self.assertEqual(provider.scope, None)
        self.assertEqual(provider.dependencies, {})

        self.assertIsInstance(graph.get('tomate.signals'), TomateNamespace)


class TestConnectDecorator(unittest.TestCase):

    @patch('tomate.signals.TomateNamespace.connect')
    def test_decorator(self, mconnect):
        from tomate.signals import subscribe

        class Dummy(object):
            subscriptions = (
                ('updated_timer', 'foo'),
            )

            @subscribe
            def __init__(self):
                super(Dummy, self).__init__()

            def foo(self):
                pass

        dummy = Dummy()

        mconnect.assert_called_once_with('updated_timer', dummy.foo)
