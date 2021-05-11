import random

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events, TimerPayload
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


@pytest.mark.parametrize(
    "event, payload",
    [
        (Events.SESSION_READY, create_session_payload(duration=random.randint(1, 100))),
        (Events.SESSION_INTERRUPT, create_session_payload(duration=random.randint(1, 100))),
        (Events.SESSION_CHANGE, create_session_payload(duration=random.randint(1, 100))),
        (Events.TIMER_UPDATE, TimerPayload(time_left=random.randint(1, 100), duration=0)),
    ],
)
def test_updates_countdown_when_session_state_changes(event, payload, bus, countdown):
    bus.send(event, payload=payload)

    assert payload.countdown in countdown.widget.get_text()
