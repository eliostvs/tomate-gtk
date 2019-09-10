import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.pomodoro import Sessions, State
from tomate.pomodoro.event import Session, connect_events
from tomate.pomodoro.session import SessionPayload
from tomate.ui.widgets import TaskButton, ModeButton


@pytest.fixture
def subject(mock_session):
    Session.receivers.clear()

    instance = TaskButton(mock_session)

    connect_events(instance)

    return instance


def test_module(graph, mocker):
    spec = "tomate.ui.taskbutton"
    package = "tomate.ui.widgets.task_button"

    scan_to_graph([package], graph)
    graph.register_factory("tomate.session", mocker.Mock)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), TaskButton)


def test_mode_button_type(subject):
    assert isinstance(subject.widget, ModeButton)


def describe_session_lifecycle():
    def test_disable_button_when_session_starts(subject):
        # when
        Session.send(State.started)

        # then
        assert subject.widget.get_sensitive() is False

    def test_enable_mode_button_when_session_stops(subject):
        # when
        Session.send(State.stopped)

        # then
        assert subject.widget.get_sensitive() is True

    def test_change_active_button_button_when_session_finishes(subject, mock_session):
        # given
        payload = SessionPayload(
            type=Sessions.shortbreak,
            sessions=[],
            state=State.finished,
            duration=0,
            task="",
        )

        # when
        Session.send(State.finished, payload=payload)

        # then
        assert subject.widget.get_selected() is Sessions.shortbreak.value
        mock_session.change.assert_called_once_with(session=Sessions.shortbreak)

    def test_buttons_be_activate_when_session_finishes(subject):
        # when
        Session.send(State.finished)

        # then
        assert subject.widget.get_sensitive() is True

    def test_change_task_when_mode_button_changes(subject, mock_session):
        # when
        subject.widget.emit("mode_changed", Sessions.longbreak.value)

        refresh_gui(0)

        # then
        mock_session.change.assert_called_once_with(session=Sessions.longbreak)
