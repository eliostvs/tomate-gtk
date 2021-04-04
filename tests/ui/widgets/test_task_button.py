import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui, assert_shortcut_called
from tomate.pomodoro import Sessions, State
from tomate.pomodoro.event import Events
from tomate.pomodoro.session import Payload as SessionPayload
from tomate.ui.widgets import TaskButton


@pytest.fixture
def subject(graph, session, shortcut_manager):
    graph.register_instance("tomate.session", session)
    graph.register_instance("tomate.ui.shortcut", shortcut_manager)
    scan_to_graph(["tomate.ui.widgets.task_button"], graph)

    shortcut_manager.disconnect("button.pomodoro", "<control>1")
    shortcut_manager.disconnect("button.shortbreak", "<control>2")
    shortcut_manager.disconnect("button.longbreak", "<control>3")

    return graph.get("tomate.ui.taskbutton")


def test_module(graph, subject):
    instance = graph.get("tomate.ui.taskbutton")

    assert isinstance(instance, TaskButton)
    assert instance is subject


def test_disables_buttons_when_session_starts(subject):
    Events.Session.send(State.started)

    assert subject.widget.get_sensitive() is False


@pytest.mark.parametrize("state", [State.finished, State.stopped])
def test_changes_selected_button_when_session_finishes(state, subject, session):
    payload = SessionPayload(
        id="",
        type=Sessions.shortbreak,
        pomodoros=0,
        state=State.finished,
        duration=0,
    )
    Events.Session.send(state, payload=payload)

    assert subject.widget.get_sensitive() is True
    assert subject.widget.get_selected() is Sessions.shortbreak.value
    session.change.assert_called_once_with(session=Sessions.shortbreak)


@pytest.mark.parametrize(
    "session_type", [Sessions.pomodoro, Sessions.shortbreak, Sessions.longbreak]
)
def test_changes_session_type_when_task_button_is_clicked(session_type, subject, session):
    subject.widget.emit("mode_changed", session_type.value)

    refresh_gui()

    session.change.assert_called_once_with(session=session_type)


@pytest.mark.parametrize("shortcut, session_type", [
    ("<control>1", Sessions.pomodoro), ("<control>2", Sessions.shortbreak), ("<control>3", Sessions.longbreak)
])
def test_shortcuts(shortcut, session_type, subject, shortcut_manager, session):
    assert_shortcut_called(shortcut_manager, shortcut)
    session.change(session=session_type)
