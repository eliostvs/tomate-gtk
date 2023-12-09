import subprocess

import gi
import pytest

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk

from tomate.pomodoro import Events, SessionType
from tomate.ui.testing import Q, create_session_payload

SECTION_NAME = "script_plugin"


@pytest.fixture
def subprocess_run(mocker, monkeypatch):
    import script

    mock = mocker.Mock(spec=subprocess.run)
    monkeypatch.setattr(script.subprocess, "run", mock)
    return mock


@pytest.fixture
def plugin(bus, config, graph):
    graph.providers.clear()
    graph.register_instance("tomate.config", config)
    graph.register_instance("tomate.bus", bus)

    from script import ScriptPlugin

    instance = ScriptPlugin()
    instance.configure(bus, graph)
    return instance


@pytest.mark.parametrize(
    "event,option",
    [
        (Events.SESSION_START, "start_command"),
        (Events.SESSION_INTERRUPT, "stop_command"),
        (Events.SESSION_END, "finish_command"),
    ],
)
def test_execute_command_when_event_is_trigger(event, option, bus, subprocess_run, config, plugin):
    command = config.get(SECTION_NAME, option)
    plugin.activate()

    bus.send(event, create_session_payload())

    subprocess_run.assert_called_once_with(command, shell=True, check=True)


@pytest.mark.parametrize(
    "event,section,session_type",
    [
        (Events.SESSION_START, "start_command", SessionType.POMODORO),
        (Events.SESSION_INTERRUPT, "stop_command", SessionType.LONG_BREAK),
        (Events.SESSION_END, "finish_command", SessionType.SHORT_BREAK),
    ],
)
def test_command_variables(event, section, session_type, bus, subprocess_run, config, plugin):
    config.set(SECTION_NAME, section, "$event $session")
    plugin.activate()

    bus.send(event, create_session_payload(type=session_type))

    subprocess_run.assert_called_once_with(f"{event.name} {session_type.name}", shell=True, check=True)


@pytest.mark.parametrize(
    "event, option",
    [
        (Events.SESSION_START, "start_command"),
        (Events.SESSION_INTERRUPT, "stop_command"),
        (Events.SESSION_END, "finish_command"),
    ],
)
def test_does_not_execute_commands_when_they_are_not_configured(event, option, bus, subprocess_run, config, plugin):
    config.remove(SECTION_NAME, option)
    plugin.activate()

    assert bus.send(event, create_session_payload()) == [False]

    subprocess_run.assert_not_called()


def test_execute_command_fail(bus, config, plugin):
    config.set(SECTION_NAME, "start_command", "fail")

    plugin.activate()

    assert bus.send(Events.SESSION_START, create_session_payload()) == [False]


class TestSettingsWindow:
    @pytest.mark.parametrize(
        "option,command",
        [
            ("start_command", "echo start"),
            ("stop_command", "echo stop"),
            ("finish_command", "echo finish"),
        ],
    )
    def test_with_custom_commands(self, option, command, plugin):
        dialog = plugin.settings_window(Gtk.Window())

        switch = Q.select(dialog.widget, Q.props("name", f"{option}_switch"))
        assert switch.props.active is True

        entry = Q.select(dialog.widget, Q.props("name", f"{option}_entry"))
        assert entry.props.text == command

    @pytest.mark.parametrize("option", ["start_command", "stop_command", "finish_command"])
    def test_without_custom_commands(self, option, config, plugin):
        config.remove_section(SECTION_NAME)
        config.save()

        assert config.has_section(SECTION_NAME) is False

        dialog = plugin.settings_window(Gtk.Window())

        switch = Q.select(dialog.widget, Q.props("name", f"{option}_switch"))
        assert switch.props.active is False

        entry = Q.select(dialog.widget, Q.props("name", f"{option}_entry"))
        assert entry.props.text == ""

    @pytest.mark.parametrize("option", ["start_command", "stop_command", "finish_command"])
    def test_disable_command(self, option, config, plugin):
        dialog = plugin.settings_window(Gtk.Window())

        switch = Q.select(dialog.widget, Q.props("name", f"{option}_switch"))
        switch.props.active = False

        entry = Q.select(dialog.widget, Q.props("name", f"{option}_entry"))
        assert entry.props.sensitive is False
        assert entry.props.text == ""

        dialog.widget.emit("response", 0)
        assert dialog.widget.props.window is None

        config.load()
        assert config.has_option(SECTION_NAME, option) is False

    @pytest.mark.parametrize("option", ["start_command", "stop_command", "finish_command"])
    def test_configure_command(self, option, config, plugin):
        config.remove(SECTION_NAME, option)

        dialog = plugin.settings_window(Gtk.Window())

        switch = Q.select(dialog.widget, Q.props("name", f"{option}_switch"))
        switch.props.active = True

        entry = Q.select(dialog.widget, Q.props("name", f"{option}_entry"))
        assert entry.props.sensitive is True
        entry.props.text = "echo changed"

        dialog.widget.emit("response", 0)
        assert dialog.widget.props.window is None

        config.load()
        assert config.get(SECTION_NAME, option) == "echo changed"

    def test_text(self, config, plugin):
        dialog = plugin.settings_window(Gtk.Window())

        expected = (
            "You can use the session and event names in your script using the"
            " <i>$session</i> and <i>$event</i> template variables."
        )
        assert Q.select(dialog.widget, Q.props("label", expected))

        assert Q.select(dialog.widget, Q.props("label", "<b>Scripts</b>"))
