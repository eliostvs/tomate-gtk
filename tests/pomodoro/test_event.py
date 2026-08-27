import gc
import uuid
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest
from gi.repository import GLib
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Bus, Event, Events, Subscriber, on


def deliver_events():
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)


class TestBus:
    def test_publish_creates_an_immutable_timestamped_event_before_delivery(self):
        event_id = uuid.UUID("12345678-1234-4abc-8def-123456789abc")
        occurred_at = datetime(2026, 8, 27, 12, 30, tzinfo=timezone.utc)
        bus = Bus(id_factory=lambda: event_id, clock=lambda: occurred_at)
        received = []
        bus.connect(Events.SESSION_START, received.append, weak=False)

        event = bus.publish(Events.SESSION_START, payload="payload")

        assert event == Event(event_id, occurred_at, Events.SESSION_START, "payload")
        assert event.occurred_at.tzinfo == timezone.utc
        assert received == []

        with pytest.raises(FrozenInstanceError):
            event.payload = "changed"

        deliver_events()

        assert received == [event]

    def test_publish_preserves_fifo_order_when_a_receiver_publishes(self):
        bus = Bus()
        received = []

        def on_start(event):
            received.append(event.type)
            bus.publish(Events.SESSION_END)

        bus.connect(Events.SESSION_START, on_start, weak=False)
        bus.connect(Events.SESSION_READY, lambda event: received.append(event.type), weak=False)
        bus.connect(Events.SESSION_END, lambda event: received.append(event.type), weak=False)

        bus.publish(Events.SESSION_START)
        bus.publish(Events.SESSION_READY)
        deliver_events()

        assert received == [Events.SESSION_START, Events.SESSION_READY, Events.SESSION_END]

    def test_publish_rejects_a_naive_clock_value(self):
        bus = Bus(clock=lambda: datetime(2026, 8, 27, 12, 30))  # noqa: DTZ001

        with pytest.raises(ValueError, match="timezone-aware"):
            bus.publish(Events.SESSION_START)

    def test_disconnect_skips_a_receiver_already_queued_for_delivery(self):
        bus = Bus()
        received = []

        bus.connect(Events.SESSION_START, received.append, weak=False)
        bus.publish(Events.SESSION_START)
        bus.disconnect(Events.SESSION_START, received.append)
        deliver_events()

        assert received == []

    def test_collected_weak_receiver_is_removed_before_delivery(self):
        bus = Bus()
        received = []

        class Receiver:
            def receive(self, event):
                received.append(event)

        receiver = Receiver()
        bus.connect(Events.SESSION_START, receiver.receive)
        bus.publish(Events.SESSION_START)
        del receiver
        gc.collect()
        deliver_events()

        assert received == []

    def test_failing_receiver_is_logged_without_stopping_later_receivers(self, caplog):
        bus = Bus()
        received = []

        def fail(_):
            raise ValueError("broken receiver")

        bus.connect(Events.SESSION_START, fail, weak=False)
        bus.connect(Events.SESSION_START, received.append, weak=False)

        event = bus.publish(Events.SESSION_START)
        deliver_events()

        assert received == [event]
        assert str(event.id) in caplog.text
        assert Events.SESSION_START.name in caplog.text

    def test_send_bridges_existing_payload_subscribers(self):
        bus = Bus()

        class Subject(Subscriber):
            @on(Events.SESSION_START)
            def receive(self, payload):
                self.payload = payload

        subject = Subject()
        subject.connect(bus)

        event = bus.send(Events.SESSION_START, payload="payload")
        deliver_events()

        assert subject.payload == "payload"
        assert event.payload == "payload"


def test_module(graph):
    scan_to_graph(["tomate.pomodoro.event"], graph)
    instance = graph.get("tomate.bus")

    assert isinstance(instance, Bus)
    assert graph.get("tomate.bus") is instance
