import pytest
import xml.etree.ElementTree as ET
from gi.repository import Gtk

from tomate.constant import State
from tomate.event import Session, Timer
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.widgets.timerframe import TimerFrame, DEFAULT_TIME_LEFT


@pytest.fixture
def task_entry(mocker):
    return mocker.Mock(widget=Gtk.Entry())


@pytest.fixture
def timer_frame(task_entry):
    return TimerFrame(task_entry)


def test_timer_frame_module(graph, task_entry):
    scan_to_graph(['tomate_gtk.widgets.timerframe'], graph)

    assert 'view.timerframe' in graph.providers

    provider = graph.providers['view.timerframe']

    assert provider.scope == SingletonScope

    graph.register_instance('view.taskentry', task_entry)

    assert isinstance(graph.get('view.timerframe'), TimerFrame)


def test_update_timer_label_when_timer_changed_with_default_timer(timer_frame):
    Timer.send(State.changed)

    markup = timer_frame.time_left_markup(DEFAULT_TIME_LEFT)
    root = ET.fromstring(markup)

    assert timer_frame.timer_label.get_text() == root.text


def test_update_timer_label_when_session_stops(timer_frame):
    Session.send(State.stopped, time_left=10)

    markup = timer_frame.time_left_markup(10)
    root = ET.fromstring(markup)

    assert timer_frame.timer_label.get_text() == root.text


def test_update_timer_label_when_session_attributes_changes(timer_frame):
    Session.send(State.changed, time_left=1)

    markup = timer_frame.time_left_markup(1)
    root = ET.fromstring(markup)

    assert timer_frame.timer_label.get_text() == root.text
