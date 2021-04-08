from collections import namedtuple
from unittest.mock import Mock

import pytest
from wiring.scanning import scan_to_graph

from tomate.ui.testing import Q, TV

PLUGIN_CATEGORY = "Default"
TestPlugin = namedtuple("TestPlugin", "name version description plugin_object")


@pytest.fixture()
def plugin_manager():
    from yapsy.PluginManager import PluginManager

    return PluginManager()


@pytest.fixture()
def enabled_plugin():
    return TestPlugin(
        name="Enabled",
        version="1.0.0",
        description="Description",
        plugin_object=Mock(has_settings=False, is_activated=True),
    )


@pytest.fixture()
def disabled_plugin():
    return TestPlugin(
        name="Disabled",
        version="2.0.0",
        description="Description",
        plugin_object=Mock(has_settings=True, is_activated=False),
    )


@pytest.fixture
def subject(graph, plugin_manager, config, mocker):
    mocker.patch("tomate.ui.dialogs.preference.Gtk.Dialog.run")

    graph.register_instance("tomate.plugin", plugin_manager)
    graph.register_instance("tomate.config", config)

    scan_to_graph(["tomate.ui.dialogs.preference"], graph)

    return graph.get("tomate.ui.preference")


def test_preference_module(graph, subject):
    from tomate.ui.dialogs import PreferenceDialog

    instance = graph.get("tomate.ui.preference")

    assert isinstance(instance, PreferenceDialog)
    assert instance is subject


def test_extension_module(graph, subject):
    from tomate.ui.dialogs import ExtensionTab

    instance = graph.get("tomate.ui.preference.extension")
    assert isinstance(instance, ExtensionTab)


def test_refresh_load_available_plugins(subject, plugin_manager, enabled_plugin, disabled_plugin):
    plugin_manager.appendPluginToCategory(enabled_plugin, PLUGIN_CATEGORY)
    plugin_manager.appendPluginToCategory(disabled_plugin, PLUGIN_CATEGORY)
    subject.run()

    plugin_list = Q.select(subject.widget, Q.name("pluginList"))
    assert plugin_list is not None
    assert TV.map(plugin_list, TV.model, len) == 2

    plugin_manager.removePluginFromCategory(enabled_plugin, PLUGIN_CATEGORY)
    plugin_manager.removePluginFromCategory(disabled_plugin, PLUGIN_CATEGORY)
    subject.run()

    assert TV.map(plugin_list, TV.model, len) == 0


@pytest.mark.parametrize(
    "plugin,row",
    [
        (
            "enabled_plugin",
            ["Enabled", True, "<b>Enabled</b> (1.0.0)\n<small>Description</small>"],
        ),
        (
            "disabled_plugin",
            ["Disabled", False, "<b>Disabled</b> (2.0.0)\n<small>Description</small>"],
        ),
    ],
)
def test_refresh_select_first_plugin(plugin, row, subject, enabled_plugin, disabled_plugin, plugin_manager):
    from tomate.ui.dialogs import PluginGrid

    plugin_manager.appendPluginToCategory(locals()[plugin], PLUGIN_CATEGORY)
    subject.run()

    rows = TV.map(
        Q.select(subject.widget, Q.name("pluginList")),
        TV.model,
        TV.rows(PluginGrid.NAME, PluginGrid.ACTIVE, PluginGrid.DETAIL),
    )
    assert rows == [row]
    assert Q.select(subject.widget, Q.name("pluginSettingsButton")).get_sensitive() is False


def test_select_plugin(subject, disabled_plugin, plugin_manager):
    plugin_manager.appendPluginToCategory(disabled_plugin, PLUGIN_CATEGORY)
    subject.run()

    TV.map(
        Q.select(subject.widget, Q.name("pluginList")),
        TV.column(Q.title("Active")),
        TV.cell_renderer(0),
        Q.emit("toggled", "0"),
    )

    assert Q.select(subject.widget, Q.name("pluginSettingsButton")).get_sensitive() is True


def test_open_plugin_settings(subject, plugin_manager, disabled_plugin):
    plugin_manager.appendPluginToCategory(disabled_plugin, "Default")

    subject.run()

    Q.select(subject.widget, Q.name("pluginSettingsButton")).emit("clicked")

    disabled_plugin.plugin_object.settings_window.assert_called_once_with(subject.widget)


def test_timer_module(graph, subject):
    from tomate.ui.dialogs import TimerTab

    instance = graph.get("tomate.ui.preference.timer")
    assert isinstance(instance, TimerTab)

    assert instance is graph.get("tomate.ui.preference.timer")


@pytest.mark.parametrize(
    "option, value",
    [
        ("pomodoro_duration", 24),
        ("shortbreak_duration", 4),
        ("longbreak_duration", 14),
    ],
)
def test_save_config_when_task_duration_change(option, value, config, subject):
    spin_button = Q.select(subject.widget, Q.name(option))
    assert spin_button is not None

    spin_button.set_value(value)
    spin_button.emit("value-changed")

    assert config.get_int("Timer", option) == value
