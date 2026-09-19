import random

import pytest

from tests.conftest import deliver_events
from tomate.pomodoro import Events, TimerPayload
from tomate.ui.testing import create_session_payload
from tomate.ui.widgets import Countdown


@pytest.fixture
def countdown(bus) -> Countdown:
    return Countdown(bus)


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
    bus.publish(event, payload=payload)

    assert payload.countdown not in countdown.widget.get_text()
    deliver_events()

    assert payload.countdown in countdown.widget.get_text()
