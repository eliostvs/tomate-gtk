import enum
import functools
import logging
from typing import Any, Callable, List, Tuple

import blinker
from wiring import SingletonScope
from wiring.scanning import register

logger = logging.getLogger(__name__)


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


Receiver = Callable[[Events, Any], Any]


@register.factory("tomate.bus", scope=SingletonScope)
class Bus:
    def __init__(self):
        self._bus = blinker.NamedSignal("tomate")

    def connect(self, event: Events, receiver: Receiver, weak: bool = True):
        self._bus.connect(receiver, sender=event, weak=weak)

    def send(self, event: Events, payload: Any = None) -> List[Any]:
        # drop receiver, index 0, from the result
        return [result[1] for result in self._bus.send(event, payload=payload)]

    def disconnect(self, event: Events, receiver: Receiver):
        self._bus.disconnect(receiver, sender=event)


def on(*events: Events):
    def wrapper(method):
        method._events = events

        @functools.wraps(method)
        def wrapped(*args, **kwargs):
            return method(*args, **kwargs)

        return wrapped

    return wrapper


class Subscriber:
    def connect(self, bus: Bus) -> None:
        for method, events in self.__methods_with_events():
            for event in events:
                logger.debug(
                    "action=connect event=%s method=%s.%s",
                    event,
                    self.__class__.__name__,
                    method.__name__,
                )
                bus.connect(event, method)

    def disconnect(self, bus: Bus):
        for method, events in self.__methods_with_events():
            for event in events:
                logger.debug(
                    "action=disconnect event=%s method=%s.%s",
                    event,
                    self.__class__.__name__,
                    method.__name__,
                )
                bus.disconnect(event, method)

    def __methods_with_events(self) -> List[Tuple[Any, List[Events]]]:
        return [
            (getattr(self, attr), getattr(getattr(self, attr), "_events"))
            for attr in dir(self)
            if hasattr(getattr(self, attr), "_events")
        ]
