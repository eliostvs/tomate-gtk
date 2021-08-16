import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events, SessionType
from tomate.ui.testing import Q, active_shortcut, create_session_payload, refresh_gui
from tomate.ui.widgets import SessionButton


@pytest.fixture
def session_button(bus, graph, session, shortcut_engine) -> SessionButton:
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.session", session)
    graph.register_instance("tomate.ui.shortcut", shortcut_engine)
    scan_to_graph(["tomate.ui.widgets.session_button"], graph)

    # clean key binds between tests
    shortcut_engine.disconnect(SessionButton.POMODORO_SHORTCUT)
    shortcut_engine.disconnect(SessionButton.SHORT_BREAK_SHORTCUT)
    shortcut_engine.disconnect(SessionButton.LONG_BREAK_SHORTCUT)

    return graph.get("tomate.ui.taskbutton")


def test_module(graph, session_button):
    instance = graph.get("tomate.ui.taskbutton")

    assert isinstance(instance, SessionButton)
    assert instance is session_button


@pytest.mark.parametrize(
    "button_name,label,tooltip_text",
    [
        (SessionButton.POMODORO_SHORTCUT.name, "Pomodoro", "Pomodoro (Ctrl+1)"),
        (SessionButton.SHORT_BREAK_SHORTCUT.name, "Short Break", "Short Break (Ctrl+2)"),
        (SessionButton.LONG_BREAK_SHORTCUT.name, "Long Break", "Long Break (Ctrl+3)"),
    ],
)
def test_buttons_content(button_name, label, tooltip_text, session_button):
    button = Q.select(session_button.widget, Q.props("name", button_name))

    assert button.props.tooltip_text == tooltip_text

    assert Q.select(button, Q.props("label", label))


def test_disables_buttons_when_session_starts(bus, session_button):
    bus.send(Events.SESSION_START)

    assert session_button.widget.props.sensitive is False


@pytest.mark.parametrize(
    "event,payload,session_type",
    [
        (Events.SESSION_INTERRUPT, create_session_payload(type=SessionType.LONG_BREAK), SessionType.LONG_BREAK),
        (Events.SESSION_READY, create_session_payload(), SessionType.POMODORO),
    ],
)
def test_selects_button_when_session_stops_and_begins(event, payload, session_type, bus, session_button, session):
    session_button.widget.props.sensitive = False

    bus.send(event, payload=payload)

    assert session_button.widget.props.sensitive is True
    assert session_button.widget.get_selected() is session_type.value


@pytest.mark.parametrize("session_type", [SessionType.POMODORO, SessionType.SHORT_BREAK, SessionType.LONG_BREAK])
def test_changes_session_when_button_is_clicked(session_type, session_button, session):
    session_button.widget.emit("mode_changed", session_type.value)

    refresh_gui()

    session.change.assert_called_once_with(session_type)


@pytest.mark.parametrize(
    "shortcut,session_type",
    [
        (SessionButton.POMODORO_SHORTCUT, SessionType.POMODORO),
        (SessionButton.SHORT_BREAK_SHORTCUT, SessionType.SHORT_BREAK),
        (SessionButton.LONG_BREAK_SHORTCUT, SessionType.LONG_BREAK),
    ],
)
def test_shortcuts(shortcut, session_type, session_button, shortcut_engine, session):
    assert active_shortcut(shortcut_engine, shortcut) is True

    session.change.assert_called_once_with(session_type)


def test_selects_button_when_session_changes(bus, session_button, session):
    bus.send(Events.SESSION_CHANGE, payload=create_session_payload(type=SessionType.SHORT_BREAK))

    assert session_button.widget.get_selected() is SessionType.SHORT_BREAK.value
