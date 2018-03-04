import xml.etree.ElementTree as ET

import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State
from tomate.event import Session, Timer
from tomate_gtk.widgets.timerframe import TimerFrame, DEFAULT_SESSION_COUNT, DEFAULT_TIME_LEFT


@pytest.fixture
def timer_frame():
    return TimerFrame()


def test_timerframe_module(graph):
    scan_to_graph(['tomate_gtk.widgets.timerframe'], graph)

    assert 'view.timerframe' in graph.providers

    provider = graph.providers['view.timerframe']

    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.timerframe'), TimerFrame)


def test_update_session_label_when_session_finishes_with_default_value(timer_frame):
    Session.send(State.finished)

    markup = timer_frame.session_markup(DEFAULT_SESSION_COUNT)
    root = ET.fromstring(markup)

    assert timer_frame.session_label.get_text() == root.text


def test_update_session_label_when_session_finishes_with_custom_value(timer_frame):
    Session.send(State.finished, sessions=10)

    markup = timer_frame.session_markup(10)
    root = ET.fromstring(markup)

    assert timer_frame.session_label.get_text() == root.text


def test_update_session_label_when_session_reset_with_custom_value(timer_frame):
    Session.send(State.finished)

    markup = timer_frame.session_markup(DEFAULT_SESSION_COUNT)
    root = ET.fromstring(markup)

    assert timer_frame.session_label.get_text() == root.text


def test_updat_timer_label_when_timer_changed_with_default_timer(timer_frame):
    Timer.send(State.changed)

    markup = timer_frame.time_left_markup(DEFAULT_TIME_LEFT)
    root = ET.fromstring(markup)

    assert timer_frame.timer_label.get_text() == root.text


def test_updat_timer_label_when_session_stops(timer_frame):
    Session.send(State.stopped, time_left=10)

    markup = timer_frame.time_left_markup(10)
    root = ET.fromstring(markup)

    assert timer_frame.timer_label.get_text() == root.text


def test_updat_timer_label_when_session_attributes_changes(timer_frame):
    Session.send(State.changed, time_left=1)

    markup = timer_frame.time_left_markup(1)
    root = ET.fromstring(markup)

    assert timer_frame.timer_label.get_text() == root.text
