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
def countdown():
    return Countdown()


def test_countdown_module(graph, countdown):
    scan_to_graph(['tomate_gtk.widgets.countdown'], graph)

    assert 'view.countdown' in graph.providers

    provider = graph.providers['view.countdown']

    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.countdown'), Countdown)


def test_update_timer_label_when_timer_changed(countdown):
    Timer.send(State.changed, payload=TimerPayload(time_left=10, duration=0))

    markup = countdown.timer_markup(format_time_left(10))
    root = ET.fromstring(markup)

    assert countdown.widget.get_text() == root.text


def test_update_timer_label_when_session_stops(countdown):
    Session.send(State.stopped, payload=TimerPayload(duration=10, time_left=10))

    markup = countdown.timer_markup(format_time_left(10))
    root = ET.fromstring(markup)

    assert countdown.widget.get_text() == root.text


def test_update_timer_label_when_session_changes(countdown):
    Session.send(State.changed, payload=TimerPayload(duration=1, time_left=1))

    markup = countdown.timer_markup(format_time_left(1))
    root = ET.fromstring(markup)

    assert countdown.widget.get_text() == root.text
