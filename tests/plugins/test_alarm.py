from os.path import dirname, join
from unittest.mock import patch

import gi
import pytest

gi.require_version("Gtk", "4.0")
gi.require_version("Gst", "1.0")

from tomate.pomodoro import Events
from tomate.ui.testing import Q

CUSTOM_ALARM = f'file://{join(dirname(dirname(__file__)), "data", "tomate", "media", "custom.ogg")}'
DEFAULT_ALARM = f'file://{join(dirname(dirname(__file__)), "data", "tomate", "media", "alarm.ogg")}'
SECTION_NAME = "alarm_plugin"
URI_OPTION_NAME = "uri"


@pytest.fixture
def plugin(bus, config, graph):
    graph.providers.clear()
    graph.register_instance("tomate.config", config)
    graph.register_instance("tomate.bus", bus)

    from alarm import AlarmPlugin

    instance = AlarmPlugin()
    instance.configure(bus, graph)
    return instance


class TestPlugin:
    def test_loads_configuration_when_is_activated(self, bus, config, plugin):
        plugin.activate()

        assert pytest.approx(plugin.player.volume, rel=1e-3) == 0.8
        assert plugin.player.file == DEFAULT_ALARM
        assert not plugin.player.repeat

    @patch("alarm.GStreamerPlayer")
    def test_plays_alarm_when_session_ends(self, player, bus, config, plugin):
        plugin.activate()

        bus.send(Events.SESSION_END)

        assert player.return_value.play.called


class TestSettingsWindow:
    def test_without_custom_alarm(self, config, plugin, toplevel):
        config.remove(SECTION_NAME, URI_OPTION_NAME)
        dialog = plugin.settings_window(toplevel)

        entry = Q.select(dialog.widget, Q.props("name", "custom_entry"))
        assert entry.props.text == ""
        assert entry.props.sensitive is False

        switch = Q.select(dialog.widget, Q.props("name", "custom_switch"))
        assert switch.props.active is False

    def test_with_custom_alarm(self, plugin, config, toplevel):
        config.set(SECTION_NAME, URI_OPTION_NAME, CUSTOM_ALARM)

        dialog = plugin.settings_window(toplevel)
        dialog.run()

        entry = Q.select(dialog.widget, Q.props("name", "custom_entry"))
        assert entry.props.text == CUSTOM_ALARM
        assert entry.props.sensitive is True

        switch = Q.select(dialog.widget, Q.props("name", "custom_switch"))
        assert switch.props.active is True

    def test_configures_custom_alarm(self, config, plugin, toplevel):
        dialog = plugin.settings_window(toplevel)

        switch = Q.select(dialog.widget, Q.props("name", "custom_switch"))
        switch.props.active = True

        entry = Q.select(dialog.widget, Q.props("name", "custom_entry"))
        assert entry.props.sensitive is True
        entry.set_text(CUSTOM_ALARM)

        dialog.widget.emit("response", 0)
        assert dialog.widget.get_visible() is False

        assert config.get(SECTION_NAME, URI_OPTION_NAME) == CUSTOM_ALARM

    def test_disables_custom_alarm(self, config, plugin, toplevel):
        config.set(SECTION_NAME, URI_OPTION_NAME, CUSTOM_ALARM)

        dialog = plugin.settings_window(toplevel)

        switch = Q.select(dialog.widget, Q.props("name", "custom_switch"))
        switch.props.active = False

        entry = Q.select(dialog.widget, Q.props("name", "custom_entry"))
        assert entry.props.text == ""
        assert entry.props.sensitive is False

        dialog.widget.emit("response", 0)
        assert dialog.widget.get_visible() is False

        assert config.has_option(SECTION_NAME, URI_OPTION_NAME) is False
