import xml.etree.ElementTree as ET

import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State
from tomate.event import Session, Timer
from tomate.utils import format_time_left
from tomate.timer import TimerPayload
from tomate_gtk.widgets import Countdown


@pytest.fixture
def subject():
    return Countdown()


def test_module(graph, subject):
    spec = 'view.countdown'

    scan_to_graph(['tomate_gtk.widgets.countdown'], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), Countdown)


def test_update_timer_label_when_timer_changed(subject):
    Timer.send(State.changed, payload=TimerPayload(time_left=10, duration=0))

    markup = subject.timer_markup(format_time_left(10))
    root = ET.fromstring(markup)

    assert subject.widget.get_text() == root.text


def test_update_timer_label_when_session_stops(subject):
    Session.send(State.stopped, payload=TimerPayload(duration=10, time_left=10))

    markup = subject.timer_markup(format_time_left(10))
    root = ET.fromstring(markup)

    assert subject.widget.get_text() == root.text


def test_update_timer_label_when_session_changes(subject):
    Session.send(State.changed, payload=TimerPayload(duration=1, time_left=1))

    markup = subject.timer_markup(format_time_left(1))
    root = ET.fromstring(markup)

    assert subject.widget.get_text() == root.text
