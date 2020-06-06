import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import State
from tomate.pomodoro.event import Events, on, Subscriber, ObservableProperty


def test_extend_subscriber():
    Events.Config.receivers.clear()

    class Subject(Subscriber):
        @on(Events.Config, [State.finished, State.stopped])
        def bar(self, sender):
            return sender

    subject = Subject()

    result = Events.Config.send(State.finished)
    assert result == [(subject.bar, State.finished)]

    result = Events.Config.send(State.stopped)
    assert result == [(subject.bar, State.stopped)]

    result = Events.Config.send(State.showed)
    assert result == []


@pytest.fixture()
def observable(mocker):
    class Subject:
        trigger = mocker.Mock()
        state = ObservableProperty("a", trigger, event="spam")
        other_state = ObservableProperty("b", trigger, "_hide")

    return Subject()


class TestObservableProperty:
    def test_observable_property_initial_value(self, observable):
        assert observable.state == "a"
        assert observable.other_state == "b"

    def test_calls_trigger_method_with_chose_event_type(self, observable):
        observable.state = "a"

        observable.trigger.assert_called_with(observable, "spam")

    def test_calls_trigger_method_with_default_event_type(self, observable):
        observable.other_state = "b"

        observable.trigger.assert_called_with(observable, "b")


def test_module(graph):
    scan_to_graph(["tomate.pomodoro.event"], graph)

    assert graph.get("tomate.events.config") is Events.Config
    assert graph.get("tomate.events.session") is Events.Session
    assert graph.get("tomate.events.timer") is Events.Timer
    assert graph.get("tomate.events.view") is Events.View
