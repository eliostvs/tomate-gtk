from __future__ import unicode_literals

import logging

import wrapt
from blinker import Namespace
from wiring import Module

logger = logging.getLogger(__name__)


class TomateNamespace(Namespace):

    def emit(self, name, **kwargs):
        signal = self[name]
        return signal.send(**kwargs)

    def connect(self, name, method):
        signal = self[name]
        signal.connect(method, weak=True)

    def disconnect(self, name, method):
        signal = self[name]
        signal.disconnect(method)


tomate_signals = TomateNamespace()

# Timer
timer_updated = tomate_signals.signal('timer_updated')
timer_finished = tomate_signals.signal('timer_finished')

# Pomodoro
session_started = tomate_signals.signal('session_started')
sessions_reseted = tomate_signals.signal('sessions_reseted')
session_interrupted = tomate_signals.signal('session_interrupted')
session_ended = tomate_signals.signal('session_ended')
task_changed = tomate_signals.signal('task_changed')

# Window
view_showed = tomate_signals.signal('view_showed')
view_hid = tomate_signals.signal('view_hid')

# Settings
setting_changed = tomate_signals.signal('setting_changed')


class Subscriber(object):

    subscriptions = ()

    def connect(self):
        for (signal, method) in self.subscriptions:
            tomate_signals.connect(signal, getattr(self, method))

            logger.debug('method %s.%s connect to signal %s.',
                         self.__class__.__name__, method, signal)

    def disconnect(self):
        for (signal, method) in self.subscriptions:
            tomate_signals.disconnect(signal, getattr(self, method))

            logger.debug('method %s.%s disconnect from signal %s.',
                         self.__class__.__name__, method, signal)


@wrapt.decorator
def subscribe(wrapped, instance, args, kwargs):
    for (signal, method) in instance.subscriptions:
        tomate_signals.connect(signal, getattr(instance, method))

        logger.debug('method %s.%s connect to signal %s.',
                     instance.__class__.__name__, method, signal)

    return wrapped(*args, **kwargs)


class SignalsProvider(Module):

    instances = {
        'tomate.signals': tomate_signals
    }
