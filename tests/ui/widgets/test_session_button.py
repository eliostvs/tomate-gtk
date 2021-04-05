import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import assert_shortcut_called, create_session_end_payload, create_session_payload, refresh_gui
from tomate.pomodoro.event import Bus, Events
from tomate.pomodoro.session import Type as SessionType
from tomate.ui.widgets import SessionButton


@pytest.fixture
def subject(graph, session, shortcut_manager):
    graph.register_instance("tomate.session", session)
    graph.register_instance("tomate.ui.shortcut", shortcut_manager)
    scan_to_graph(["tomate.ui.widgets.session_button"], graph)

    shortcut_manager.disconnect("button.pomodoro", "<control>1")
    shortcut_manager.disconnect("button.shortbreak", "<control>2")
    shortcut_manager.disconnect("button.longbreak", "<control>3")

    return graph.get("tomate.ui.taskbutton")


def test_module(graph, subject):
    instance = graph.get("tomate.ui.taskbutton")

    assert isinstance(instance, SessionButton)
    assert instance is subject


def test_disables_buttons_when_session_starts(subject):
    Bus.send(Events.SESSION_START)

    assert subject.widget.get_sensitive() is False


@pytest.mark.parametrize(
    "event,payload",
    [
        (Events.SESSION_INTERRUPT, create_session_payload(type=SessionType.SHORT_BREAK)),
        (
            Events.SESSION_END,
            create_session_end_payload(type=SessionType.SHORT_BREAK, previous=create_session_payload()),
        ),
    ],
)
def test_changes_selected_button_when_session_finishes(event, payload, subject, session):
    Bus.send(event, payload=payload)

    assert subject.widget.get_sensitive() is True
    assert subject.widget.get_selected() is SessionType.SHORT_BREAK.value
    session.change.assert_called_once_with(session=SessionType.SHORT_BREAK)


@pytest.mark.parametrize("session_type", [SessionType.POMODORO, SessionType.SHORT_BREAK, SessionType.LONG_BREAK])
def test_changes_session_type_when_task_button_is_clicked(session_type, subject, session):
    subject.widget.emit("mode_changed", session_type.value)

    refresh_gui()

    session.change.assert_called_once_with(session=session_type)


@pytest.mark.parametrize(
    "shortcut,session_type",
    [
        ("<control>1", SessionType.POMODORO),
        ("<control>2", SessionType.SHORT_BREAK),
        ("<control>3", SessionType.LONG_BREAK),
    ],
)
def test_shortcuts(shortcut, session_type, subject, shortcut_manager, session):
    assert_shortcut_called(shortcut_manager, shortcut)
    session.change(session=session_type)
