import xml.etree.ElementTree as ET

import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.pomodoro import State
from tomate.pomodoro.event import Session, Timer
from tomate.pomodoro.timer import TimerPayload, format_time_left
from tomate.ui.widgets import Countdown


@pytest.fixture
def subject():
    return Countdown()


def format_time(time_left: int) -> str:
    markup = Countdown.timer_markup(format_time_left(time_left))
    return ET.fromstring(markup).text


def test_module(graph, subject):
    spec = "tomate.ui.countdown"
    package = "tomate.ui.widgets.countdown"

    scan_to_graph([package], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), Countdown)


def test_update_timer_label_when_timer_changes(subject):
    # given
    time_left = 10
    payload = TimerPayload(time_left=time_left, duration=0)
    expected = format_time(time_left)

    # when
    Timer.send(State.changed, payload=payload)

    # then
    assert subject.widget.get_text() == expected


def test_update_timer_label_when_session_stops(subject):
    # given
    time_left = 10
    payload = TimerPayload(duration=10, time_left=time_left)
    expected = format_time(time_left)

    # when
    Session.send(State.stopped, payload=payload)

    # then
    assert subject.widget.get_text() == expected


def test_update_timer_label_when_session_changes(subject):
    # given
    time_left = 1
    payload = TimerPayload(duration=1, time_left=time_left)
    expected = format_time(time_left)

    # when
    Session.send(State.changed, payload=payload)

    # then
    assert subject.widget.get_text() == expected
