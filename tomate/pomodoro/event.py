import enum
import functools
import logging

import blinker
from wiring.scanning import register

logger = logging.getLogger(__name__)

bus = blinker.NamedSignal("tomate")
register.instance("tomate.bus")(bus)


@enum.unique
class Events(enum.Enum):
    TIMER_START = 0
    TIMER_UPDATE = 1
    TIMER_STOP = 2
    TIMER_END = 3

    SESSION_START = 4
    SESSION_INTERRUPT = 5
    SESSION_CHANGE = 6
    SESSION_END = 7
    SESSION_RESET = 8

    WINDOW_SHOW = 9
    WINDOW_HIDE = 10

    CONFIG_CHANGE = 11


def on(*events: Events):
    def wrapper(method):
        method._events = events

        @functools.wraps(method)
        def wrapped(*args, **kwargs):
            return method(*args, **kwargs)

        return wrapped

    return wrapper


class Subscriber:
    def connect(self, bus: blinker.Signal) -> None:
        for method, events in self.__methods_with_events():
            for event in events:
                logger.debug(
                    "action=connect event=%s method=%s.%s",
                    event,
                    self.__class__.__name__,
                    method.__name__,
                )
                bus.connect(method, sender=event)

    def disconnect(self, bus: blinker.Signal):
        for method, events in self.__methods_with_events():
            for event in events:
                logger.debug(
                    "action=disconnect event=%s method=%s.%s",
                    event,
                    self.__class__.__name__,
                    method.__name__,
                )
                bus.disconnect(method, sender=event)

    def __methods_with_events(self):
        return [
            (getattr(self, attr), getattr(getattr(self, attr), "_events"))
            for attr in dir(self)
            if getattr(getattr(self, attr), "_events", None)
        ]
