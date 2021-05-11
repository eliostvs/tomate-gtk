from wiring.scanning import scan_to_graph

from tomate.pomodoro import Bus, Events, Subscriber, on


class TestBus:
    def test_connect_receiver(self, bus, mocker):
        def side_effect(*_, payload):
            return payload

        receiver = mocker.Mock(side_effect=side_effect)
        bus.connect(Events.SESSION_START, receiver, weak=False)

        assert bus.send(Events.SESSION_START, payload="payload") == ["payload"]

    def test_disconnect_receiver(self, bus, mocker):
        receiver = mocker.Mock()
        bus.connect(Events.SESSION_START, receiver, weak=False)
        bus.disconnect(Events.SESSION_START, receiver)

        assert bus.send(Events.SESSION_START, payload="payload") == []


def test_subscriber(bus):
    class Subject(Subscriber):
        @on(Events.TIMER_START, Events.SESSION_START)
        def bar(self, **__) -> bool:
            return True

    subject = Subject()
    subject.connect(bus)

    result = bus.send(Events.TIMER_START, "timer_start")
    assert len(result) == 1 and result[0] is True

    result = bus.send(Events.SESSION_START)
    assert len(result) == 1 and result[0] is True

    assert bus.send(Events.WINDOW_SHOW) == []

    subject.disconnect(bus)

    assert bus.send(Events.TIMER_START) == []
    assert bus.send(Events.SESSION_START) == []


def test_module(graph):
    scan_to_graph(["tomate.pomodoro.event"], graph)
    instance = graph.get("tomate.bus")

    assert isinstance(instance, Bus)
    assert graph.get("tomate.bus") is instance
