from dataclasses import FrozenInstanceError

import pytest
from gi.repository import GLib

from tests.conftest import EVENT_ID, EVENT_OCCURRED_AT
from tomate.pomodoro.event import Event, Events, Subscriber, on


def deliver_events():
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)


class TestBus:
    def test_connect_registers_a_receiver_for_its_event_type(self, bus):
        received = []

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, receive)
        bus.publish(Events.SESSION_READY)
        deliver_events()

        assert received == []

    def test_is_connect_reports_whether_a_receiver_is_connected(self, bus):
        def receive(_):
            pass

        assert not bus.is_connect(Events.SESSION_START, receive)

        bus.connect(Events.SESSION_START, receive)

        assert bus.is_connect(Events.SESSION_START, receive)
        assert not bus.is_connect(Events.SESSION_READY, receive)

    def test_connect_does_not_register_the_same_receiver_twice(self, bus):
        received = []

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, receive)
        bus.connect(Events.SESSION_START, receive)

        event = bus.publish(Events.SESSION_START)
        deliver_events()

        assert received == [event]

    def test_publish_creates_and_delivers_an_immutable_timestamped_event(self, bus):
        received = []

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, receive)

        event = bus.publish(Events.SESSION_START, payload="payload")

        assert event == Event(EVENT_ID, EVENT_OCCURRED_AT, Events.SESSION_START, "payload")
        assert received == []

        with pytest.raises(FrozenInstanceError):
            event.payload = "changed"

        deliver_events()

        assert received == [event]

    def test_publish_does_not_deliver_to_receivers_connected_after_publication(self, bus):
        received = []

        def receive(event):
            received.append(event)

        bus.publish(Events.SESSION_START)
        bus.connect(Events.SESSION_START, receive)
        deliver_events()

        assert received == []

    def test_disconnect_skips_a_receiver_already_queued_for_delivery(self, bus):
        received = []

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, receive)
        bus.publish(Events.SESSION_START)
        bus.disconnect(Events.SESSION_START, receive)
        deliver_events()

        assert received == []

    def test_disconnect_prevents_future_delivery(self, bus):
        received = []

        def receive(event):
            received.append(event)

        bus.connect(Events.SESSION_START, receive)
        bus.disconnect(Events.SESSION_START, receive)
        bus.publish(Events.SESSION_START)
        deliver_events()

        assert received == []

    def test_a_failing_receiver_does_not_block_other_receivers(self, bus, caplog):
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


class TestSubscriber:
    def test_connects_decorated_methods_to_their_events(self, bus):
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

    def test_connects_one_method_to_each_of_its_declared_events(self, bus):
        received = []

        class Subject(Subscriber):
            @on(Events.SESSION_START, Events.SESSION_END)
            def receive(self, event):
                received.append(event)

        subject = Subject()
        subject.connect(bus)

        start = bus.publish(Events.SESSION_START)
        end = bus.publish(Events.SESSION_END)
        deliver_events()

        assert received == [start, end]

    def test_reconnect_does_not_duplicate_delivery(self, bus):
        received = []

        class Subject(Subscriber):
            @on(Events.SESSION_START)
            def receive(self, event):
                received.append(event)

        subject = Subject()
        subject.connect(bus)
        subject.connect(bus)

        event = bus.publish(Events.SESSION_START)
        deliver_events()

        assert received == [event]

    def test_disconnect_removes_all_decorated_method_receivers(self, bus):
        received = []

        class Subject(Subscriber):
            @on(Events.SESSION_START)
            def receive_start(self, event):
                received.append(event)

            @on(Events.SESSION_END)
            def receive_end(self, event):
                received.append(event)

        subject = Subject()
        subject.connect(bus)
        subject.disconnect(bus)

        bus.publish(Events.SESSION_START)
        bus.publish(Events.SESSION_END)
        deliver_events()

        assert received == []
