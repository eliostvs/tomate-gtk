import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Config, Events
from tomate.ui.dialogs import (ExtensionTab, PluginGrid, PreferenceDialog,
                               TimerTab)
from tomate.ui.testing import TV, Q


@pytest.fixture
def preference(bus, plugin_engine, config, mocker) -> PreferenceDialog:
    mocker.patch("tomate.ui.dialogs.preference.Gtk.Dialog.run")
    return PreferenceDialog(TimerTab(config), ExtensionTab(bus, config, plugin_engine))


def test_preference_module(graph, bus, config, plugin_engine):
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.plugin", plugin_engine)
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.ui.dialogs.preference"], graph)
    instance = graph.get("tomate.ui.preference")

    assert isinstance(instance, PreferenceDialog)
    assert graph.get("tomate.ui.preference") is instance


def test_refresh_reload_plugins(preference, plugin_engine):
    plugin_engine.collect()
    preference.run()

    plugin_list = Q.select(preference.widget, Q.props("name", "plugin.list"))
    assert Q.map(plugin_list, TV.model, len) == 2

    for plugin in plugin_engine.all():
        plugin_engine.remove(plugin)

    preference.run()

    assert Q.map(plugin_list, TV.model, len) == 0


@pytest.mark.parametrize(
    "plugin,row,columns",
    [
        (
            "PluginA",
            0,
            ["PluginA", False, "<b>PluginA</b> (1.0)\n<small>Description A</small>"],
        ),
        (
            "PluginB",
            1,
            ["PluginB", True, "<b>PluginB</b> (2.0)\n<small>Description B</small>"],
        ),
    ],
)
def test_initial_plugin_list(plugin, row, columns, preference, plugin_engine):
    plugin_engine.collect()
    preference.run()

    def get_columns(tree_store: Gtk.TreeStore):
        return [tree_store[row][column] for column in (PluginGrid.NAME, PluginGrid.ACTIVE, PluginGrid.DETAIL)]

    assert Q.map(Q.select(preference.widget, Q.props("name", "plugin.list")), TV.model, get_columns) == columns
    assert Q.select(preference.widget, Q.props("name", "plugin.settings")).props.sensitive is False


def test_open_plugin_settings(preference, plugin_engine):
    plugin_engine.collect()
    preference.run()

    Q.map(
        Q.select(preference.widget, Q.props("name", "plugin.list")),
        TV.column(Q.props("title", "Active")),
        TV.cell_renderer(0),
        Q.emit("toggled", 0),
    )

    settings_button = Q.select(preference.widget, Q.props("name", "plugin.settings"))
    assert settings_button.props.sensitive is True

    settings_button.emit("clicked")
    plugin_a = plugin_engine.lookup("PluginA")
    assert plugin_a.plugin_object.parent == preference.widget


def test_connect_and_disconnect_plugins(bus, plugin_engine, preference):
    plugin_engine.collect()
    preference.run()

    result = bus.send(Events.WINDOW_SHOW)
    assert len(result) == 1 and result[0] == "plugin_b"

    def toggle_plugin(row: int):
        Q.map(
            Q.select(preference.widget, Q.props("name", "plugin.list")),
            TV.column(Q.props("title", "Active")),
            TV.cell_renderer(0),
            Q.emit("toggled", row),
        )

    toggle_plugin(0)
    toggle_plugin(1)

    result = bus.send(Events.WINDOW_SHOW)
    assert len(result) == 1 and result[0] == "plugin_a"


@pytest.mark.parametrize(
    "duration_name,option,value",
    [
        ("duration.pomodoro", Config.DURATION_POMODORO, 24),
        ("duration.shortbreak", Config.DURATION_SHORT_BREAK, 4),
        ("duration.longbreak", Config.DURATION_LONG_BREAK, 14),
    ],
)
def test_save_config_when_task_duration_change(duration_name, option, value, config, preference):
    spin_button = Q.select(preference.widget, Q.props("name", duration_name))
    assert spin_button is not None

    spin_button.props.value = value
    spin_button.emit("value-changed")

    assert config.get_int(Config.DURATION_SECTION, option) == value
