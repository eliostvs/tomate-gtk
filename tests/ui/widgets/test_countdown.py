import random
import xml.etree.ElementTree as ET

import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import create_session_payload
from tomate.pomodoro.event import Events
from tomate.pomodoro.timer import Payload as TimerPayload, format_time_left


@pytest.fixture
def subject(graph, bus):
    graph.register_instance("tomate.bus", bus)
    scan_to_graph(["tomate.ui.widgets.countdown"], graph)
    return graph.get("tomate.ui.countdown")


def test_module(graph, subject):
    from tomate.ui.widgets import Countdown

    instance = graph.get("tomate.ui.countdown")

    assert isinstance(instance, Countdown)
    assert instance is subject


@pytest.mark.parametrize("event", [Events.SESSION_INTERRUPT, Events.SESSION_CHANGE])
def test_updates_countdown_when_session_state_changes(event, subject, bus):
    duration = random.randint(1, 100)

    bus.send(event, payload=create_session_payload(duration=duration))

    assert subject.widget.get_text() == format_time(duration)


def test_updates_countdown_when_timer_changes(subject, bus):
    time_left = random.randint(1, 100)

    bus.send(Events.TIMER_UPDATE, payload=TimerPayload(time_left=time_left, duration=0))

    assert subject.widget.get_text() == format_time(time_left)


def format_time(time_left: int) -> str:
    from tomate.ui.widgets import Countdown

    markup = Countdown.timer_markup(format_time_left(time_left))
    return ET.fromstring(markup).text
