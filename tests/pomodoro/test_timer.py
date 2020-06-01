import pytest
from blinker import signal
from wiring.scanning import scan_to_graph

from tests.conftest import run_loop_for
from tomate.pomodoro import State
from tomate.pomodoro.timer import TimerPayload, format_time_left, SIXTY_SECONDS


@pytest.fixture()
def dispatcher():
    return signal('timer')


@pytest.fixture()
def subject(graph, dispatcher):
    graph.register_instance("tomate.events.timer", dispatcher)

    scan_to_graph(["tomate.pomodoro.timer"], graph)

    return graph.get("tomate.timer")


class TestTimerStart:
    def test_not_starts_when_timer_is_already_running(self, subject):
        subject.state = State.started

        assert not subject.start(SIXTY_SECONDS)

    @pytest.mark.parametrize(
        "state",
        [State.finished, State.stopped]
    )
    def test_starts_when_timer_not_started_yet(self, state, subject, dispatcher):
        subject.state = state
        called = False

        def subscriber(sender, payload):
            assert sender is State.started
            assert payload == TimerPayload(time_left=60, duration=60)

            nonlocal called
            called = True

        dispatcher.connect(subscriber, sender=State.started)

        result = subject.start(SIXTY_SECONDS)

        assert result is True
        assert called is True


class TestTimerStop:
    @pytest.mark.parametrize(
        "state",
        [State.finished, State.stopped]
    )
    def test_not_stops_when_timer_is_not_running(self, state, subject):
        subject.state = state
        assert not subject.stop()

    def test_stops_when_timer_is_running(self, subject, dispatcher):
        called = False

        def subscriber(sender, payload):
            assert sender is State.stopped
            assert payload == TimerPayload(time_left=0, duration=0)

            nonlocal called
            called = True

        dispatcher.connect(subscriber, sender=State.stopped)

        subject.start(SIXTY_SECONDS)
        result = subject.stop()

        assert result is True
        assert called is True


class TestTimerEnd:
    @pytest.mark.parametrize(
        "state",
        [State.finished, State.stopped]
    )
    def test_not_ends_when_timer_is_not_running(self, state, subject):
        subject.state = state
        assert not subject.end()

    def test_ends_when_timer_is_running(self, subject, dispatcher):
        finished_called = False
        changed_called = False

        def changed_subscriber(sender, payload):
            assert sender is State.changed
            assert payload == TimerPayload(time_left=0, duration=1)

            nonlocal changed_called
            changed_called = True

        dispatcher.connect(changed_subscriber, sender=State.changed)

        def finished_subscriber(sender, payload):
            assert sender is State.finished
            assert payload == TimerPayload(time_left=0, duration=1)

            nonlocal finished_called
            finished_called = True

        dispatcher.connect(finished_subscriber, sender=State.finished)

        subject.start(1)
        run_loop_for(1)
        result = subject.end()

        assert result is True
        assert finished_called is True
        assert changed_called is True


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


def test_module(graph, subject):
    assert graph.get('tomate.timer') is subject


@pytest.mark.parametrize(
    "seconds,time_formatted",
    [(25 * 60, "25:00"), (15 * 60, "15:00"), (5 * 60, "05:00")],
)
def test_format_time_left(seconds, time_formatted):
    assert time_formatted == format_time_left(seconds)
