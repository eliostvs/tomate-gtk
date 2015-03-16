from __future__ import division, unicode_literals

from gi.repository import GObject
from wiring import implements, inject, Interface, Module, SingletonScope

from .enums import State
from .utils import fsm

# Borrowed from Tomatoro create by Pierre Quillery.
# https://github.com/dandelionmood/Tomatoro
# Thanks Pierre!


class ITimer(Interface):

    state = ''

    time_ratio = ''

    time_left = ''

    def start(seconds):
        pass

    def update():
        pass

    def stop():
        pass

    def end():
        pass


@implements(ITimer)
class Timer(object):

    @inject(signals='tomate.signals')
    def __init__(self, signals):
        self.signals = signals
        self.state = State.stopped
        self.reset()

    @fsm(target=State.running,
         source=[State.stopped])
    def start(self, seconds):
        self.__seconds = self.time_left = seconds

        GObject.timeout_add(1000, self.update)

        return True

    def update(self):
        if self.state != State.running:
            return False

        if self.time_left <= 0:
            return self.end()

        self.time_left -= 1

        self.emit('timer_updated')

        return True

    @fsm(target=State.stopped,
         source=[State.running])
    def stop(self):
        self.reset()

        return True

    def timer_is_up(self):
        return self.time_left <= 0

    @fsm(target=State.stopped,
         source=[State.running],
         conditions=[timer_is_up],
         exit=lambda i: i.emit('timer_finished'))
    def end(self):
        self.reset()

        return False

    @property
    def time_ratio(self):
        try:
            ratio = round(1.0 - self.time_left / self.__seconds, 1)

        except ZeroDivisionError:
            ratio = 0

        return ratio

    def emit(self, signal):
        self.signals.emit(signal,
                          time_left=self.time_left,
                          time_ratio=self.time_ratio)

    def reset(self):
        self.__seconds = self.time_left = 0


class TimerProvider(Module):

    factories = {
        'tomate.timer': (Timer, SingletonScope),
    }
