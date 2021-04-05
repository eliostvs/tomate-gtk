import blinker
from wiring.scanning import scan_to_graph

from tomate.pomodoro.event import Subscriber, on

EVENT_FOO = "foo"
EVENT_BAR = "bar"


def test_subscriber(bus):
    class Subject(Subscriber):
        @on(bus, [EVENT_FOO, EVENT_BAR])
        def bar(self, sender):
            return sender

    subject = Subject()

    result = bus.send(EVENT_BAR)
    assert result == [(subject.bar, EVENT_BAR)]

    result = bus.send(EVENT_FOO)
    assert result == [(subject.bar, EVENT_FOO)]

    result = bus.send("NO")
    assert result == []


def test_module(graph):
    scan_to_graph(["tomate.pomodoro.event"], graph)

    assert isinstance(graph.get("tomate.bus"), blinker.Signal)
