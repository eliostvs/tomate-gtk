import random
import xml.etree.ElementTree as ET

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import State
from tomate.pomodoro.event import Events
from tomate.pomodoro.session import Payload as SessionPayload
from tomate.pomodoro.timer import Payload as TimerPayload, format_time_left
from tomate.ui.widgets import Countdown


@pytest.fixture
def subject(graph):
    scan_to_graph(["tomate.ui.widgets.countdown"], graph)
    return graph.get("tomate.ui.countdown")


def test_module(graph, subject):
    instance = graph.get("tomate.ui.countdown")

    assert isinstance(instance, Countdown)
    assert instance is subject


@pytest.mark.parametrize("event", [State.stopped, State.changed])
def test_updates_countdown_when_session_state_changes(event, subject):
    duration = random.randint(1, 100)

    Events.Session.send(
        event,
        payload=SessionPayload(
            id="", state="", type="", pomodoros=0, duration=duration
        ),
    )

    assert subject.widget.get_text() == format_time(duration)


def test_updates_countdown_when_timer_changes(subject):
    time_left = random.randint(1, 100)

    Events.Timer.send(
        State.changed, payload=TimerPayload(time_left=time_left, duration=0)
    )

    assert subject.widget.get_text() == format_time(time_left)


def format_time(time_left: int) -> str:
    markup = Countdown.timer_markup(format_time_left(time_left))
    return ET.fromstring(markup).text
