import enum
import logging
import weakref
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

from gi.repository import GLib
from wiring import SingletonScope
from wiring.scanning import register

logger = logging.getLogger(__name__)

T = TypeVar("T")
Receiver = Callable[["Event[Any]"], Any]
Clock = Callable[[], datetime]
IdFactory = Callable[[], UUID]


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
    id: UUID
    occurred_at: datetime
    type: Events
    payload: T | None


class Subscription:
    def __init__(self, receiver: Receiver, weak: bool):
        self.active = True
        self._receiver: Receiver | weakref.ReferenceType[Receiver]
        if weak:
            self._receiver = self._weak_reference(receiver)
        else:
            self._receiver = receiver

    @staticmethod
    def _weak_reference(receiver: Receiver) -> weakref.ReferenceType[Receiver]:
        if getattr(receiver, "__self__", None) is not None:
            return weakref.WeakMethod(receiver)
        return weakref.ref(receiver)

    def resolve(self) -> Receiver | None:
        if isinstance(self._receiver, weakref.ReferenceType):
            return self._receiver()
        return self._receiver

    def matches(self, receiver: Receiver) -> bool:
        return self.resolve() == receiver


@register.factory("tomate.bus", scope=SingletonScope)
class Bus:
    def __init__(self, id_factory=uuid4, clock=None):
        self._id_factory: IdFactory = id_factory
        self._clock: Clock = clock or (lambda: datetime.now(timezone.utc))
        self._subscriptions: dict[Events, list[Subscription]] = {event: [] for event in Events}
        self._queue: deque[tuple[Event[Any], tuple[Subscription, ...]]] = deque()
        self._delivery_scheduled = False

    def connect(self, event: Events, receiver: Receiver, weak: bool = True) -> None:
        if not self.is_connect(event, receiver):
            self._subscriptions[event].append(Subscription(receiver, weak))

    def is_connect(self, event: Events, receiver: Receiver) -> bool:
        return any(
            subscription.active and subscription.matches(receiver) for subscription in self._subscriptions[event]
        )

    def publish(self, event_type: Events, payload: T | None = None) -> Event[T]:
        occurred_at = self._clock()
        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise ValueError("clock must return a timezone-aware datetime")
        event = Event(self._id_factory(), occurred_at.astimezone(timezone.utc), event_type, payload)
        subscriptions = tuple(subscription for subscription in self._subscriptions[event_type] if subscription.active)
        self._queue.append((event, subscriptions))
        if not self._delivery_scheduled:
            self._delivery_scheduled = True
            GLib.idle_add(self._deliver, priority=GLib.PRIORITY_DEFAULT_IDLE)
        return event

    def send(self, event: Events, payload: T | None = None) -> Event[T]:
        """Temporarily bridge legacy publishers to typed deferred publication."""
        return self.publish(event, payload)

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
        self._legacy_receivers: list[tuple[Events, Receiver]] = []
        for method, events in self.__methods_with_events():
            for event in events:
                logger.debug(
                    "action=connect event=%s method=%s.%s",
                    event,
                    self.__class__.__name__,
                    method.__name__,
                )

                def receiver(envelope: Event[Any], method=method):
                    return method(payload=envelope.payload)

                bus.connect(event, receiver)
                self._legacy_receivers.append((event, receiver))

    def disconnect(self, bus: Bus) -> None:
        for event, receiver in getattr(self, "_legacy_receivers", []):
            logger.debug("action=disconnect event=%s receiver=%r", event, receiver)
            bus.disconnect(event, receiver)
        self._legacy_receivers = []

    def __methods_with_events(self) -> list[tuple[Any, tuple[Events, ...]]]:
        return [
            (getattr(self, attr), getattr(self, attr)._events)
            for attr in dir(self)
            if hasattr(getattr(self, attr), "_events")
        ]
