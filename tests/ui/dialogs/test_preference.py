from collections import namedtuple
from unittest.mock import Mock

import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tomate.ui.dialogs import TimerTab, GridPlugin
from tomate.ui.test import Q, T

PACKAGE = "tomate.ui.dialogs.preference"


@pytest.fixture()
def plugin_manager():
    from yapsy.PluginManager import PluginManager

    return PluginManager()


@pytest.fixture()
def window():
    return Gtk.Label()


TestPlugin = namedtuple("TestPlugin", "name version description plugin_object")


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


class TestExtensionTab:
    SPEC = "tomate.ui.preference.extension"
    CATEGORY = "Default"

    @pytest.fixture
    def subject(self, graph, real_config, plugin_manager):
        scan_to_graph([PACKAGE], graph)

        graph.register_instance("tomate.plugin", plugin_manager)
        graph.register_instance("tomate.config", real_config)

        return graph.get(self.SPEC)

    def test_module(self, graph, subject):
        from tomate.ui.dialogs import ExtensionTab

        instance = graph.get(self.SPEC)

        assert isinstance(instance, ExtensionTab)
        assert instance is subject

    def test_refresh_load_available_plugins(
        self, subject, plugin_manager, enabled_plugin, disabled_plugin
    ):
        plugin_manager.appendPluginToCategory(enabled_plugin, self.CATEGORY)
        plugin_manager.appendPluginToCategory(disabled_plugin, self.CATEGORY)
        subject.refresh()

        plugin_list = Q.select(subject.widget, Q.name("pluginList"))
        assert plugin_list is not None
        assert T.query(plugin_list, T.model, len) == 2

        plugin_manager.removePluginFromCategory(enabled_plugin, self.CATEGORY)
        plugin_manager.removePluginFromCategory(disabled_plugin, self.CATEGORY)
        subject.refresh()

        assert T.query(plugin_list, T.model, len) == 0

    @pytest.mark.parametrize(
        "plugin, row",
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
    def test_refresh_select_first_plugin(
        self, plugin, row, subject, enabled_plugin, disabled_plugin, plugin_manager
    ):
        plugin_manager.appendPluginToCategory(locals()[plugin], self.CATEGORY)
        subject.refresh()

        columns = T.items_columns(GridPlugin.NAME, GridPlugin.ACTIVE, GridPlugin.DETAIL)
        assert T.query(Q.select(subject.widget, Q.name("pluginList")), T.model, columns) == [row]
        assert Q.select(subject.widget, Q.name("pluginSettingsButton")).get_sensitive() is False

    def test_select_plugin(self, subject, disabled_plugin, plugin_manager):
        plugin_manager.appendPluginToCategory(disabled_plugin, self.CATEGORY)
        subject.refresh()

        T.query(
            Q.select(subject.widget, Q.name("pluginList")),
            T.column("Active"),
            T.cell(0),
            Q.emit("toggled", "0"),
        )

        assert Q.select(subject.widget, Q.name("pluginSettingsButton")).get_sensitive() is True

    def test_open_plugin_settings(self, subject, plugin_manager, disabled_plugin):
        plugin_manager.appendPluginToCategory(disabled_plugin, "Default")
        toplevel = Gtk.Label()
        subject.set_toplevel(toplevel)
        subject.refresh()

        Q.select(subject.widget, Q.name("pluginSettingsButton")).emit("clicked")

        disabled_plugin.plugin_object.settings_window.assert_called_once_with(toplevel)


class TestPreference:
    SPEC = "tomate.ui.preference"

    @pytest.fixture
    def mock_extension_tab(self, mocker):
        return mocker.Mock(widget=Gtk.Label())

    @pytest.fixture
    def mock_timer_tab(self, mocker):
        return mocker.Mock(widget=Gtk.Label())

    @pytest.fixture
    def subject(self, graph, plugin_manager, real_config, mock_proxy):
        graph.register_instance("tomate.plugin", plugin_manager)
        graph.register_instance("tomate.config", real_config)
        graph.register_instance("tomate.proxy", mock_proxy)

        scan_to_graph([PACKAGE], graph)

        return graph.get(self.SPEC)

    def test_module(self, graph, subject):
        from tomate.ui.dialogs import PreferenceDialog

        instance = graph.get(self.SPEC)

        assert isinstance(instance, PreferenceDialog)
        assert instance is subject

    def test_stack_the_extensions(self, subject, mock_timer_tab, mock_extension_tab):
        from tomate.ui.dialogs import PreferenceDialog

        subject = PreferenceDialog(mock_timer_tab, mock_extension_tab)
        subject.set_visible(True)

        subject.emit("response", 0)

        assert not subject.get_visible()
        mock_extension_tab.set_toplevel.assert_called_once_with(subject)


class TestTimerTab:
    SPEC = "tomate.ui.preference.timer"

    @pytest.fixture
    def subject(self, graph, real_config):
        graph.register_instance("tomate.config", real_config)
        scan_to_graph([PACKAGE], graph)
        return graph.get(self.SPEC)

    def test_module(self, graph, subject):
        instance = graph.get(self.SPEC)

        assert isinstance(instance, TimerTab)
        assert instance is subject

    @pytest.mark.parametrize(
        "option, value",
        [
            ("pomodoro_duration", 24),
            ("shortbreak_duration", 4),
            ("longbreak_duration", 14),
        ],
    )
    def test_save_config_when_task_duration_change(self, option, value, real_config, subject):
        spin_button = Q.select(subject.widget, Q.name(option))
        assert spin_button is not None

        spin_button.set_value(value)
        spin_button.emit("value-changed")

        assert real_config.get_int("Timer", option) == value
