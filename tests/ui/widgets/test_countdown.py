import random
import xml.etree.ElementTree as ET

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events, TimerPayload, format_time_left
from tomate.ui.testing import create_session_payload
from tomate.ui.widgets import Countdown


@pytest.fixture
def countdown(bus, graph) -> Countdown:
    graph.register_instance("tomate.bus", bus)
    scan_to_graph(["tomate.ui.widgets.countdown"], graph)
    return graph.get("tomate.ui.countdown")


def test_module(countdown, graph):
    instance = graph.get("tomate.ui.countdown")

    assert isinstance(instance, Countdown)
    assert instance is countdown


@pytest.mark.parametrize("event", [Events.SESSION_INTERRUPT, Events.SESSION_CHANGE])
def test_updates_countdown_when_session_state_changes(event, bus, countdown):
    duration = random.randint(1, 100)

    bus.send(event, payload=create_session_payload(duration=duration))

    assert countdown.widget.get_text() == format_time(duration)


def test_updates_countdown_when_timer_changes(bus, countdown):
    time_left = random.randint(1, 100)

    payload = TimerPayload(time_left=time_left, duration=0)
    bus.send(Events.TIMER_UPDATE, payload=payload)

    assert countdown.widget.get_text() == format_time(time_left)


def format_time(time_left: int) -> str:
    markup = Countdown.timer_markup(format_time_left(time_left))
    return ET.fromstring(markup).text
