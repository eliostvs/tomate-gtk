import pytest
from wiring.scanning import scan_to_graph

from tomate.core import State
from tomate.core.event import (
    on,
    Subscriber,
    SubscriberMeta,
    methods_with_events,
    disconnect_events,
)


@pytest.fixture()
def subject(mock_session, mock_timer):
    class Foo(object):
        @on(mock_session, [State.finished])
        def bar(self, sender):
            return sender

        @on(mock_timer, [State.finished, State.changed])
        def spam(self, sender):
            return sender

    return Foo()


def test_return_events_and_states_bind_with_the_method(
    subject, mock_session, mock_timer
):
    assert subject.bar._events == [(mock_session, State.finished)]

    assert subject.spam._events == [
        (mock_timer, State.finished),
        (mock_timer, State.changed),
    ]


def test_return_methods_that_has_events(subject):
    SubscriberMeta(str("name"), (object,), {})

    assert [subject.bar, subject.spam] == methods_with_events(subject)


def test_connect_event_with_the_method(mocker):
    mock_event_a = mocker.Mock()
    mock_event_b = mocker.Mock()

    class Subject(Subscriber):
        @on(mock_event_a, [State.finished, State.stopped])
        @on(mock_event_b, [State.changed])
        def bar(self, sender):
            return sender

    subject = Subject()

    mock_event_a.connect.assert_any_call(subject.bar, sender=State.finished, weak=False)
    mock_event_a.connect.assert_any_call(subject.bar, sender=State.stopped, weak=False)
    mock_event_b.connect.assert_called_with(
        subject.bar, sender=State.changed, weak=False
    )


def test_disconnect_bind_events(mocker):
    mock_event_a = mocker.Mock()
    mock_event_b = mocker.Mock()

    class Subject(Subscriber):
        @on(mock_event_a, [State.finished, State.stopped])
        @on(mock_event_b, [State.changed])
        def bar(self, sender):
            return sender

    subject = Subject()

    disconnect_events(subject)

    mock_event_a.disconnect.assert_any_call(subject.bar, sender=State.finished)
    mock_event_a.disconnect.assert_any_call(subject.bar, sender=State.stopped)
    mock_event_b.disconnect.assert_called_with(subject.bar, sender=State.changed)


def test_raise_attribute_error_when_key_not_found_in_the_namespace():
    from tomate.core.event import Events

    with pytest.raises(AttributeError):
        Events.Foo


def test_events_be_accessible_as_dictionary_and_attributes():
    import tomate.core.event as e

    assert e.Session == e.Events.Session
    assert e.Session == e.Events.Session


def test_module(graph):
    scan_to_graph(["tomate.core.event"], graph)

    assert sorted(list(graph.providers)) == sorted(
        [
            "tomate.events.setting",
            "tomate.events.session",
            "tomate.events.timer",
            "tomate.events.view",
        ]
    )
