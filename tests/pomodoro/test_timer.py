import pytest
from wiring.scanning import scan_to_graph

from pomodoro import SECONDS_IN_A_MINUTE
from tests.conftest import run_loop_for
from tomate.pomodoro import State
from tomate.pomodoro.timer import TimerPayload, format_time_left


@pytest.fixture()
def subject(graph, timer_dispatcher):
    graph.register_instance("tomate.events.timer", timer_dispatcher)

    scan_to_graph(["tomate.pomodoro.timer"], graph)

    return graph.get("tomate.timer")


def test_module(graph, subject):
    assert graph.get('tomate.timer') is subject


class TestTimerStart:
    def test_doesnt_start_when_timer_is_already_running(self, subject):
        subject.state = State.started

        assert not subject.start(SECONDS_IN_A_MINUTE)

    @pytest.mark.parametrize(
        "state",
        [State.finished, State.stopped]
    )
    def test_starts_when_timer_not_started_yet(self, state, subject, timer_dispatcher, mocker):
        subject.state = state

        subscriber = mocker.Mock()
        timer_dispatcher.connect(subscriber, sender=State.started, weak=False)

        result = subject.start(SECONDS_IN_A_MINUTE)

        assert result is True
        subscriber.assert_called_once_with(State.started, payload=TimerPayload(time_left=60, duration=60))


class TestTimerStop:
    @pytest.mark.parametrize(
        "state",
        [State.finished, State.stopped]
    )
    def test_doesnt_stop_when_timer_is_not_running(self, state, subject):
        subject.state = state
        assert not subject.stop()

    def test_stops_when_timer_is_running(self, subject, timer_dispatcher, mocker):
        subscriber = mocker.Mock()
        timer_dispatcher.connect(subscriber, sender=State.stopped, weak=False)

        subject.start(SECONDS_IN_A_MINUTE)
        result = subject.stop()

        assert result is True
        subscriber.assert_called_once_with(State.stopped, payload=TimerPayload(time_left=0, duration=0))


class TestTimerEnd:
    @pytest.mark.parametrize(
        "state",
        [State.finished, State.stopped]
    )
    def test_doesnt_end_when_timer_is_not_running(self, state, subject):
        subject.state = state
        assert not subject.end()

    def test_ends_when_timer_is_running(self, subject, timer_dispatcher, mocker):
        changed = mocker.Mock()
        timer_dispatcher.connect(changed, sender=State.changed, weak=False)

        finished = mocker.Mock()
        timer_dispatcher.connect(finished, sender=State.finished, weak=False)

        subject.start(1)
        run_loop_for(2)

        changed.assert_called_once_with(State.changed, payload=TimerPayload(time_left=0, duration=1))
        finished.assert_called_once_with(State.finished, payload=TimerPayload(time_left=0, duration=1))


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
