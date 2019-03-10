import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.core.constant import State
from tomate.core.timer import Timer, TimerPayload, format_time_left


@pytest.fixture()
def subject(mocker):
    from tomate.core.timer import Timer

    return Timer(dispatcher=mocker.Mock())


class TestEventPayload:
    @pytest.mark.parametrize(
        "duration,time_left,ratio",
        [(100, 99, 0.0), (100, 90, 0.1), (100, 50, 0.5), (100, 0, 1.0)],
    )
    def test_remaining_ratio(self, duration, time_left, ratio):
        # given
        payload = TimerPayload(duration=duration, time_left=time_left)

        # then
        assert payload.elapsed_ratio == ratio

    @pytest.mark.parametrize(
        "duration,time_left,percent",
        [(100, 100, 100.0), (100, 99, 95.0), (100, 95, 95.0), (100, 94, 90.0)],
    )
    def test_remaining_percent(self, duration, time_left, percent):
        # given
        payload = TimerPayload(duration=duration, time_left=time_left)

        # then
        assert payload.elapsed_percent == percent


class TestTimerStop:
    def test_not_be_able_to_stop_when_timer_is_not_running(self, subject):
        # given
        subject.state = State.stopped

        # then
        assert not subject.stop()

    def test_be_able_to_stop_when_timer_is_running(self, subject):
        # given
        subject.state = State.started

        # then
        assert subject.stop()
        assert subject.state == State.stopped


class TestTimerStart:
    def test_not_be_able_to_start_when_timer_is_already_running(self, subject):
        # given
        subject.state = State.started

        # then
        assert not subject.start(1)

    def test_be_able_to_start_when_timer_is_stopped(self, subject):
        # given
        subject.state = State.stopped

        # then
        assert subject.start(1)

    def test_be_able_to_start_when_timer_is_finished(self, subject):
        # given
        subject.state = State.finished

        # then
        assert subject.start(1)

    def test_update_time_left_and_duration_when_timer_start(self, subject):
        # given
        subject.state = State.finished

        # when
        subject.start(5)

        # then
        assert subject.time_left == 5
        assert subject.duration == 5

    def test_trigger_started_event_when_timer_start(self, subject):
        subject.start(10)

        subject._dispatcher.send.assert_called_with(
            State.started, payload=TimerPayload(time_left=10, duration=10)
        )


class TestTimerUpdate:
    def test_not_update_when_timer_is_not_started(self, subject):
        # given
        subject.state = State.stopped

        # then
        assert subject._update() is False

    def test_decrease_the_time_left_after_update(self, subject):
        # given
        duration = 2

        # when
        subject.start(duration)

        assert subject._update()
        assert subject.time_left == 1

    def test_keep_duration_after_update(self, subject):
        # given
        duration = 10

        # when
        subject.start(duration)

        # then
        assert subject._update()

        assert subject.duration == duration

    def test_trigger_changed_event_after_update(self, subject):
        # when
        subject.start(10)

        subject._update()

        # then
        subject._dispatcher.send.assert_called_with(
            State.changed, payload=TimerPayload(time_left=9, duration=10)
        )


class TestTimerEnd:
    def test_trigger_finished_event_when_time_ends(self, subject):
        # given
        subject.start(1)

        # when
        subject._update()
        subject._update()

        # then
        subject._dispatcher.send.assert_called_with(
            State.finished, payload=TimerPayload(time_left=0, duration=1)
        )


def test_module(graph, mocker):
    spec = "tomate.timer"
    package = "tomate.core.timer"

    scan_to_graph([package], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    graph.register_factory("tomate.events.timer", mocker.Mock)

    assert isinstance(graph.get(spec), Timer)


@pytest.mark.parametrize(
    "seconds, time_formatted",
    [(25 * 60, "25:00"), (15 * 60, "15:00"), (5 * 60, "05:00")],
)
def test_format_seconds_in_string_with_minutes_and_seconds(seconds, time_formatted):
    assert time_formatted == format_time_left(seconds)
