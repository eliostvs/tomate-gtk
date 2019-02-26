import pytest
from conftest import refresh_gui
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State, Sessions
from tomate.event import Session, connect_events
from tomate.session import SessionPayload
from tomate_gtk.widgets import TaskButton
from tomate_gtk.widgets.mode_button import ModeButton


@pytest.fixture
def subject(session):
    Session.receivers.clear()

    instance = TaskButton(session)

    connect_events(instance)

    return instance


def test_module(graph, session):
    spec = "view.taskbutton"

    scan_to_graph(["tomate_gtk.widgets.task_button"], graph)
    graph.register_instance("tomate.session", session)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), TaskButton)


def test_should_be_a_mode_button(subject):
    assert isinstance(subject.widget, ModeButton)


class TestSessionStart:
    def test_buttons_should_be_deactivate_when_session_starts(self, subject):
        Session.send(State.started)

        assert subject.widget.get_sensitive() is False


class TestSessionStop:
    def test_buttons_should_be_activate_when_session_stops(self, subject):
        Session.send(State.stopped)

        assert subject.widget.get_sensitive() is True


class TestSessionFinished:
    def test_change_button_when_session_finishes(self, subject):
        payload = SessionPayload(
            type=Sessions.shortbreak,
            sessions=[],
            state=State.finished,
            duration=0,
            task="",
        )

        Session.send(State.finished, payload=payload)

        assert subject.widget.get_selected() is Sessions.shortbreak.value
        subject.session.change.assert_called_once_with(session=Sessions.shortbreak)

    def test_buttons_should_be_activate_when_session_finishes(self, subject):
        Session.send(State.finished)

        assert subject.widget.get_sensitive() is True


def test_change_task_when_mode_button_changes(subject):
    subject.widget.emit("mode_changed", Sessions.longbreak.value)

    refresh_gui(0)

    subject.session.change.assert_called_once_with(session=Sessions.longbreak)
