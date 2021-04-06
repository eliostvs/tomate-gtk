import blinker
from wiring.scanning import scan_to_graph

from tomate.pomodoro.event import Events, Subscriber, on


def test_subscriber(bus):
    class Subject(Subscriber):
        @on(Events.TIMER_START, Events.SESSION_START)
        def bar(self, sender):
            return sender

    subject = Subject()
    subject.connect(bus)

    result = bus.send(Events.TIMER_START)
    assert result == [(subject.bar, Events.TIMER_START)]

    result = bus.send(Events.SESSION_START)
    assert result == [(subject.bar, Events.SESSION_START)]

    result = bus.send("NO")
    assert result == []


def test_module(graph):
    scan_to_graph(["tomate.pomodoro.event"], graph)

    assert isinstance(graph.get("tomate.bus"), blinker.Signal)
