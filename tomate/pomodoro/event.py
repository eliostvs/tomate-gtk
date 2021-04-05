import enum
import functools
import logging

from blinker import NamedSignal
from wiring.scanning import register

logger = logging.getLogger(__name__)

Bus = NamedSignal("Tomate")


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


def on(event, senders):
    def wrapper(func):
        if not hasattr(func, "_has_event"):
            func._has_event = True
            func._events = []

        for each in senders:
            func._events.append((event, each))

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapped

    return wrapper


def methods_with_events(obj):
    return [getattr(obj, attr) for attr in dir(obj) if getattr(getattr(obj, attr), "_has_event", False) is True]


def connect_events(obj):
    for method in methods_with_events(obj):
        for (event, sender) in method._events:
            logger.debug(
                "action=connect event=%s.%s method=%s.%s",
                event.name,
                sender,
                obj.__class__.__name__,
                method.__name__,
            )
            event.connect(method, sender=sender, weak=False)


def disconnect_events(obj):
    for method in methods_with_events(obj):
        for (event, sender) in method._events:
            logger.debug(
                "action=disconnect event=%s.%s method=%s.%s",
                event.name,
                sender,
                obj.__class__.__name__,
                method.__name__,
            )
            event.disconnect(method, sender=sender)


class SubscriberMeta(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        connect_events(obj)
        return obj


class Subscriber(metaclass=SubscriberMeta):
    pass


register.instance("tomate.bus")(Bus)
