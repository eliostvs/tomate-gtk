import blinker
import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro.event import Events
from tomate.pomodoro.timer import Payload as TimerPayload, State, Timer, format_time_left
from tomate.ui.test import run_loop_for


def create_bus():
    return blinker.NamedSignal("Test")


def test_module(graph):
    graph.register_instance("tomate.bus", create_bus())
    scan_to_graph(["tomate.pomodoro.timer"], graph)

    instance = graph.get("tomate.timer")

    assert isinstance(instance, Timer)


class TestTimerStart:
    def test_does_not_start_when_timer_is_already_running(self):
        subject = Timer(create_bus())
        subject.state = State.STARTED

        assert not subject.start(60)

    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_starts_when_timer_not_started_yet(self, state, mocker):
        bus = create_bus()
        subject = Timer(bus)
        subject.state = state

        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.TIMER_START, weak=False)

        result = subject.start(60)

        assert result is True
        subscriber.assert_called_once_with(Events.TIMER_START, payload=TimerPayload(time_left=60, duration=60))


class TestTimerStop:
    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_does_not_stop_when_timer_is_not_running(self, state):
        subject = Timer(create_bus())
        subject.state = state

        assert not subject.stop()

    def test_stops_when_timer_is_running(self, mocker):
        bus = create_bus()
        subject = Timer(bus)
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.TIMER_STOP, weak=False)

        subject.start(60)
        result = subject.stop()

        assert result is True
        assert subject.is_running() is False
        subscriber.assert_called_once_with(Events.TIMER_STOP, payload=TimerPayload(time_left=0, duration=0))


class TestTimerEnd:
    @pytest.mark.parametrize("state", [State.ENDED, State.STOPPED])
    def test_does_not_end_when_timer_is_not_running(self, state):
        subject = Timer(create_bus())
        subject.state = state

        assert not subject.end()

    def test_ends_when_time_is_up(self, mocker):
        bus = create_bus()
        subject = Timer(bus)
        changed = mocker.Mock()
        subject._bus.connect(changed, sender=Events.TIMER_UPDATE, weak=False)

        finished = mocker.Mock()
        bus.connect(finished, sender=Events.TIMER_END, weak=False)

        subject.start(1)
        run_loop_for(2)

        assert subject.is_running() is False
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
        [(100, 99, 0.0), (100, 90, 0.1), (100, 50, 0.5), (100, 0, 1.0)],
    )
    def test_elapsed_ratio(self, duration, time_left, ratio):
        payload = TimerPayload(duration=duration, time_left=time_left)

        assert payload.elapsed_ratio == ratio

    @pytest.mark.parametrize(
        "duration,time_left,percent",
        [
            (100, 0, 100.0),
            (100, 96, 0),
            (100, 95, 10.0),
            (100, 90, 10.0),
            (100, 89, 10.0),
            (100, 88, 10.0),
            (100, 86, 10),
            (100, 85, 20),
            (100, 84, 20),
            (100, 80, 20),
        ],
    )
    def test_elapsed_percent(self, duration, time_left, percent):
        payload = TimerPayload(duration=duration, time_left=time_left)

        assert payload.elapsed_percent == percent


@pytest.mark.parametrize(
    "seconds,time_formatted",
    [(25 * 60, "25:00"), (15 * 60, "15:00"), (5 * 60, "05:00")],
)
def test_format_time_left(seconds, time_formatted):
    assert time_formatted == format_time_left(seconds)
