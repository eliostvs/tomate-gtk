import pytest
from conftest import refresh_gui
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State, Sessions
from tomate.event import Session, connect_events
from tomate.session import Session as ModelSession, SessionPayload
from tomate_gtk.widgets import TaskButton
from tomate_gtk.widgets.mode_button import ModeButton


@pytest.fixture
def mock_session(mocker):
    return mocker.Mock(spec=ModelSession)


@pytest.fixture
def task_button(mock_session):
    Session.receivers.clear()

    instance = TaskButton(mock_session)
    connect_events(instance)

    return instance


def test_task_button_module(graph, mocker):
    scan_to_graph(["tomate_gtk.widgets.task_button"], graph)

    assert "view.taskbutton" in graph.providers

    provider = graph.providers["view.taskbutton"]

    assert provider.scope == SingletonScope

    graph.register_factory("tomate.session", mocker.Mock)

    assert isinstance(graph.get("view.taskbutton"), TaskButton)


def test_button_should_be_a_mode_button_widget(task_button):
    assert isinstance(task_button.widget, ModeButton)


def test_buttons_should_be_activate_when_session_finishes(task_button):
    Session.send(State.finished)

    assert task_button.mode_button.get_sensitive() is True


def test_buttons_should_be_deactivate_when_session_starts(task_button):
    Session.send(State.started)

    assert task_button.mode_button.get_sensitive() is False


def test_buttons_should_be_activate_when_session_stops(task_button):
    Session.send(State.stopped)

    assert task_button.mode_button.get_sensitive() is True


def test_change_button_when_session_finishes(task_button):
    payload = SessionPayload(
        type=Sessions.shortbreak, sessions=[], state=State.finished, duration=0, task=""
    )

    Session.send(State.finished, payload=payload)

    assert task_button.mode_button.get_selected() is Sessions.shortbreak.value
    task_button.session.change.assert_called_once_with(session=Sessions.shortbreak)


def test_change_task_when_mode_button_changes(task_button):
    task_button.mode_button.emit("mode_changed", Sessions.longbreak.value)

    refresh_gui(0)

    task_button.session.change.assert_called_once_with(session=Sessions.longbreak)
