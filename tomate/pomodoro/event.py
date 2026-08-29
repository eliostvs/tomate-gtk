import enum
import logging
import weakref
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generic, TypeVar

from gi.repository import GLib
from wiring import SingletonScope, inject
from wiring.scanning import register

from .clock import Clock
from .id import IDFactory

logger = logging.getLogger(__name__)

T = TypeVar("T")
Receiver = Callable[["Event[Any]"], Any]


@enum.unique
class Events(enum.Enum):
    TIMER_START = 0
    TIMER_UPDATE = 1
    TIMER_STOP = 2
    TIMER_END = 3

    SESSION_READY = 4
    SESSION_START = 5
    SESSION_INTERRUPT = 6
    SESSION_CHANGE = 7
    SESSION_END = 8
    SESSION_RESET = 9

    WINDOW_SHOW = 10
    WINDOW_HIDE = 11

    CONFIG_CHANGE = 12


@dataclass(frozen=True, slots=True)
class Event(Generic[T]):
    id: str
    occurred_at: datetime
    type: Events
    payload: T | None


class Subscription:
    def __init__(self, receiver: Receiver):
        self.active = True
        self._receiver = self._weak_reference(receiver)

    @staticmethod
    def _weak_reference(receiver: Receiver) -> weakref.ReferenceType[Receiver]:
        if getattr(receiver, "__self__", None) is not None:
            return weakref.WeakMethod(receiver)
        return weakref.ref(receiver)

    def resolve(self) -> Receiver | None:
        return self._receiver()

    def matches(self, receiver: Receiver) -> bool:
        return self.resolve() == receiver


@register.factory("tomate.bus", scope=SingletonScope)
class Bus:
    @inject(clock="tomate.clock", id_factory="tomate.id_factory")
    def __init__(self, clock: Clock, id_factory: IDFactory):
        self._clock = clock
        self._id_factory = id_factory
        self._subscriptions: dict[Events, list[Subscription]] = {event: [] for event in Events}
        self._queue: deque[tuple[Event[Any], tuple[Subscription, ...]]] = deque()
        self._delivery_scheduled = False

    def connect(self, event: Events, receiver: Receiver) -> None:
        if not self.is_connect(event, receiver):
            self._subscriptions[event].append(Subscription(receiver))

    def is_connect(self, event: Events, receiver: Receiver) -> bool:
        return any(
            subscription.active and subscription.matches(receiver) for subscription in self._subscriptions[event]
        )

    def publish(self, event_type: Events, payload: T | None = None) -> Event[T]:
        event = Event(self._id_factory.new(), self._clock.now(), event_type, payload)
        subscriptions = tuple(subscription for subscription in self._subscriptions[event_type] if subscription.active)

        self._queue.append((event, subscriptions))

        if not self._delivery_scheduled:
            self._delivery_scheduled = True
            GLib.idle_add(self._deliver, priority=GLib.PRIORITY_DEFAULT_IDLE)

        return event

    def disconnect(self, event: Events, receiver: Receiver) -> None:
        subscriptions = self._subscriptions[event]

        for subscription in subscriptions:
            if subscription.matches(receiver):
                subscription.active = False

        self._subscriptions[event] = [subscription for subscription in subscriptions if subscription.active]

    def _deliver(self) -> bool:
        while self._queue:
            event, subscriptions = self._queue.popleft()
            for subscription in subscriptions:
                receiver = subscription.resolve()
                if not subscription.active or receiver is None:
                    continue
                try:
                    receiver(event)
                except Exception:
                    logger.exception(
                        "action=event_delivery_failed event_id=%s event_type=%s receiver=%r",
                        event.id,
                        event.type.name,
                        receiver,
                    )
        self._delivery_scheduled = False
        return False


def on(*events: Events):
    def wrapper(method):
        method._events = events
        return method

    return wrapper


class Subscriber:
    def connect(self, bus: Bus) -> None:
        self.disconnect(bus)

        self._receivers: list[tuple[Events, Receiver]] = []

        for method, events in self.__methods_with_events():
            for event in events:
                logger.debug(
                    "action=connect event=%s method=%s.%s",
                    event,
                    self.__class__.__name__,
                    method.__name__,
                )

                def receiver(envelope: Event[Any], method=method):
                    return method(envelope)

                bus.connect(event, receiver)
                self._receivers.append((event, receiver))

    def disconnect(self, bus: Bus) -> None:
        for event, receiver in getattr(self, "_receivers", []):
            logger.debug("action=disconnect event=%s receiver=%r", event, receiver)
            bus.disconnect(event, receiver)
        self._receivers = []

    def __methods_with_events(self) -> list[tuple[Any, tuple[Events, ...]]]:
        return [
            (getattr(self, attr), getattr(self, attr)._events)
            for attr in dir(self)
            if hasattr(getattr(self, attr), "_events")
        ]
