import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events, Timer, TimerPayload
from tomate.pomodoro.timer import State
from tomate.ui.testing import run_loop_for


def test_module(bus, graph):
    graph.register_instance("tomate.bus", bus)
    scan_to_graph(["tomate.pomodoro.timer"], graph)

    instance = graph.get("tomate.timer")

    assert isinstance(instance, Timer)


class TestTimerStart:
    def test_does_not_start_when_timer_is_already_running(self, bus):
        timer = Timer(bus)
        timer.state = State.STARTED

        assert not timer.start(60)

    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_starts_when_timer_not_started_yet(self, bus, mocker, state):
        timer = Timer(bus)
        timer.state = state

        subscriber = mocker.Mock()
        bus.connect(Events.TIMER_START, subscriber, weak=False)

        result = timer.start(60)

        assert result is True
        subscriber.assert_called_once_with(Events.TIMER_START, payload=TimerPayload(time_left=60, duration=60))


class TestTimerStop:
    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_does_not_stop_when_timer_is_not_running(self, bus, state):
        timer = Timer(bus)
        timer.state = state

        assert not timer.stop()

    def test_stops_when_timer_is_running(self, bus, mocker):
        timer = Timer(bus)
        subscriber = mocker.Mock()
        bus.connect(Events.TIMER_STOP, subscriber, weak=False)

        timer.start(60)
        result = timer.stop()

        assert result is True
        assert timer.is_running() is False
        subscriber.assert_called_once_with(Events.TIMER_STOP, payload=TimerPayload(time_left=0, duration=0))


class TestTimerEnd:
    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_does_not_end_when_timer_is_not_running(self, bus, state):
        timer = Timer(bus)
        timer.state = state

        assert not timer.end()

    def test_ends_when_time_is_up(self, bus, mocker):
        timer = Timer(bus)
        changed = mocker.Mock()
        timer._bus.connect(Events.TIMER_UPDATE, changed, weak=False)

        finished = mocker.Mock()
        bus.connect(Events.TIMER_END, finished, weak=False)

        timer.start(1)
        run_loop_for(2)

        assert timer.is_running() is False
        changed.assert_called_once_with(Events.TIMER_UPDATE, payload=TimerPayload(time_left=0, duration=1))
        finished.assert_called_once_with(Events.TIMER_END, payload=TimerPayload(time_left=0, duration=1))


class TestTimerPayload:
    @pytest.mark.parametrize(
        "duration,time_left,ratio",
        [(100, 99, 0.99), (100, 90, 0.9), (100, 50, 0.5), (100, 0, 0.0)],
    )
    def test_remaining_ratio(self, duration, time_left, ratio):
        payload = TimerPayload(duration=duration, time_left=time_left)

        assert payload.remaining_ratio == ratio

    @pytest.mark.parametrize(
        "duration,time_left,ratio",
        [
            (100, 100, 0.0),
            (100, 99, 0.01),
            (100, 98, 0.02),
            (100, 97, 0.03),
            (100, 96, 0.04),
            (100, 95, 0.05),
            (100, 94, 0.06),
            (100, 93, 0.07),
            (100, 92, 0.08),
            (100, 91, 0.09),
            (100, 90, 0.1),
            (100, 89, 0.11),
            (100, 50, 0.5),
            (100, 15, 0.85),
            (100, 10, 0.9),
            (100, 5, 0.95),
            (100, 0, 1.0),
        ],
    )
    def test_elapsed_ratio(self, duration, time_left, ratio):
        payload = TimerPayload(duration=duration, time_left=time_left)

        assert payload.elapsed_ratio == ratio

    @pytest.mark.parametrize(
        "duration,time_left,percent",
        [
            (100, 100, 0.0),
            (100, 99, 0.0),
            (100, 98, 0.0),
            (100, 97, 0.0),
            (100, 96, 0.0),
            (100, 95, 5.0),
            (100, 94, 5.0),
            (100, 93, 5.0),
            (100, 92, 5.0),
            (100, 91, 5.0),
            (100, 90, 10.0),
            (100, 89, 10.0),
            (100, 6, 90.0),
            (100, 5, 95.0),
            (100, 4, 95.0),
            (100, 3, 95.0),
            (100, 2, 95.0),
            (100, 1, 95.0),
            (100, 0, 100.0),
        ],
    )
    def test_elapsed_percent(self, duration, time_left, percent):
        payload = TimerPayload(duration=duration, time_left=time_left)

        assert payload.elapsed_percent == percent

    @pytest.mark.parametrize(
        "seconds,formatted",
        [
            (25 * 60, "25:00"),
            (15 * 60, "15:00"),
            (5 * 60, "05:00"),
        ],
    )
    def test_payload_markup(self, seconds, formatted):
        payload = TimerPayload(time_left=seconds, duration=0)

        assert payload.format == formatted
