import gc
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest
from gi.repository import GLib
from wiring.scanning import scan_to_graph

from tests.conftest import EVENT_ID, EVENT_OCCURRED_AT, TestClock, TestIDFactory
from tomate.pomodoro import Bus, Event, Events, Subscriber, on


def deliver_events():
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)


class TestBus:
    def test_exposes_publish_without_the_legacy_send_bridge(self, bus):

        assert callable(bus.publish)
        assert not hasattr(bus, "send")

    def test_publish_creates_an_immutable_timestamped_event_before_delivery(self):
        event_id = "12345678-1234-4abc-8def-123456789abc"
        occurred_at = datetime(2026, 8, 27, 12, 30, tzinfo=timezone.utc)
        bus = Bus(TestClock(occurred_at), TestIDFactory(event_id))
        received = []

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, receive)

        event = bus.publish(Events.SESSION_START, payload="payload")

        assert event == Event(event_id, occurred_at, Events.SESSION_START, "payload")
        assert event.occurred_at.tzinfo == timezone.utc
        assert received == []

        with pytest.raises(FrozenInstanceError):
            event.payload = "changed"

        deliver_events()

        assert received == [event]

    def test_publish_preserves_fifo_order_when_a_receiver_publishes(self, bus):
        received = []

        def on_start(event):
            received.append(event.type)
            bus.publish(Events.SESSION_END)

        def on_ready(event):
            received.append(event.type)

        def on_end(event):
            received.append(event.type)

        bus.connect(Events.SESSION_START, on_start)
        bus.connect(Events.SESSION_READY, on_ready)
        bus.connect(Events.SESSION_END, on_end)

        bus.publish(Events.SESSION_START)
        bus.publish(Events.SESSION_READY)
        deliver_events()

        assert received == [Events.SESSION_START, Events.SESSION_READY, Events.SESSION_END]

    def test_disconnect_skips_a_receiver_already_queued_for_delivery(self, bus):
        received = []

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, receive)
        bus.publish(Events.SESSION_START)
        bus.disconnect(Events.SESSION_START, receive)
        deliver_events()

        assert received == []

    def test_collected_weak_receiver_is_removed_before_delivery(self, bus):
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

    def test_failing_receiver_is_logged_without_stopping_later_receivers(self, bus, caplog):
        received = []

        def fail(_):
            raise ValueError("broken receiver")

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, fail)
        bus.connect(Events.SESSION_START, receive)

        event = bus.publish(Events.SESSION_START)
        deliver_events()

        assert received == [event]
        assert str(event.id) in caplog.text
        assert Events.SESSION_START.name in caplog.text

    def test_subscriber_receives_the_typed_event_envelope(self, bus):

        class Subject(Subscriber):
            @on(Events.SESSION_START)
            def receive(self, event: Event[str]):
                self.event = event

        subject = Subject()
        subject.connect(bus)

        event = bus.publish(Events.SESSION_START, payload="payload")
        deliver_events()

        assert subject.event is event
        assert subject.event.type is Events.SESSION_START
        assert subject.event.payload == "payload"


def test_module(graph):
    graph.register_instance("tomate.clock", TestClock(EVENT_OCCURRED_AT))
    graph.register_instance("tomate.id_factory", TestIDFactory(EVENT_ID))
    scan_to_graph(["tomate.pomodoro.event"], graph)
    instance = graph.get("tomate.bus")

    assert isinstance(instance, Bus)
    assert graph.get("tomate.bus") is instance
