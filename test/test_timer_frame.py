import xml.etree.ElementTree as ET

import pytest
from tomate.constant import State
from tomate.event import Session, Timer
from tomate.utils import format_time_left
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.widgets import TimerFrame


@pytest.fixture
def timer_frame():
    return TimerFrame()


def test_timer_frame_module(graph, timer_frame):
    scan_to_graph(['tomate_gtk.widgets.timer_frame'], graph)

    assert 'view.timerframe' in graph.providers

    provider = graph.providers['view.timerframe']

    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.timerframe'), TimerFrame)


def test_update_timer_label_when_timer_changed(timer_frame):
    Timer.send(State.changed, time_left=10)

    markup = timer_frame.timer_markup(format_time_left(10))
    root = ET.fromstring(markup)

    assert timer_frame.widget.get_text() == root.text


def test_update_timer_label_when_session_stops(timer_frame):
    Session.send(State.stopped, duration=10)

    markup = timer_frame.timer_markup(format_time_left(10))
    root = ET.fromstring(markup)

    assert timer_frame.widget.get_text() == root.text


def test_update_timer_label_when_session_changes(timer_frame):
    Session.send(State.changed, duration=1)

    markup = timer_frame.timer_markup(format_time_left(1))
    root = ET.fromstring(markup)

    assert timer_frame.widget.get_text() == root.text
