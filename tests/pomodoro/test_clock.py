from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import TestClock


def test_system_clock_returns_a_utc_aware_datetime():
    from tomate.pomodoro.clock import SystemClock

    occurred_at = SystemClock().now()

    assert occurred_at.tzinfo is timezone.utc


def test_test_clock_normalizes_an_aware_datetime_to_utc():
    clock = TestClock(datetime(2026, 8, 27, 14, 30, tzinfo=timezone(timedelta(hours=2))))

    assert clock.now() == datetime(2026, 8, 27, 12, 30, tzinfo=timezone.utc)


def test_test_clock_rejects_a_naive_datetime():
    with pytest.raises(ValueError, match="timezone-aware"):
        TestClock(datetime(2026, 8, 27, 12, 30))  # noqa: DTZ001


def test_clock_protocol_describes_test_clock():
    now =  datetime(2026, 8, 27, 12, 30, tzinfo=timezone.utc)

    assert TestClock(now).now() == now
