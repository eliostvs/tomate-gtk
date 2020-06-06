from collections import namedtuple

import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tests.conftest import set_config
from tomate.ui.dialogs import TimerTab, GridPlugin

PACKAGE = "tomate.ui.dialogs.preference"


@pytest.fixture()
def plugin_manager():
    from yapsy.PluginManager import PluginManager

    return PluginManager()


class TestExtensionTab:
    SPEC = "tomate.ui.preference.extension"
    CATEGORY = "Default"

    @pytest.fixture
    def enabled_plugin(self, mocker):
        plugin = mocker.Mock()
        plugin.name = "Enabled"
        plugin.version = "1.0.0"
        plugin.description = "Description"
        plugin.plugin_object.has_settings = False
        plugin.plugin_object.is_activated = True
        return plugin

    @pytest.fixture
    def disabled_plugin(self, mocker):
        plugin = mocker.Mock()
        plugin.name = "Disabled"
        plugin.version = "1.0.0"
        plugin.description = "Description"
        plugin.plugin_object.has_settings = True
        plugin.plugin_object.is_activated = False
        return plugin

    @pytest.fixture
    def subject(self, graph, mock_config, plugin_manager, enabled_plugin):
        scan_to_graph([PACKAGE], graph)

        graph.register_instance("tomate.plugin", plugin_manager)
        graph.register_instance("tomate.config", mock_config)

        return graph.get(self.SPEC)

    def test_module(self, graph, subject):
        from tomate.ui.dialogs import ExtensionTab

        instance = graph.get(self.SPEC)

        assert isinstance(instance, ExtensionTab)
        assert instance is subject

    def test_clean_plugin_list(
        self, subject, plugin_manager, enabled_plugin, disabled_plugin
    ):
        plugin_manager.appendPluginToCategory(enabled_plugin, self.CATEGORY)
        plugin_manager.appendPluginToCategory(disabled_plugin, self.CATEGORY)
        subject.refresh()
        assert subject.plugin_model.iter_n_children() == 2

        plugin_manager.removePluginFromCategory(enabled_plugin, self.CATEGORY)
        plugin_manager.removePluginFromCategory(disabled_plugin, self.CATEGORY)
        subject.refresh()
        assert subject.plugin_list.get_model().iter_n_children() == 0

    def test_refreshes_select_first_plugin(
        self, subject, plugin_manager, enabled_plugin
    ):
        plugin_manager.appendPluginToCategory(enabled_plugin, self.CATEGORY)
        subject.refresh()

        model, selected = subject.plugin_list.get_selection().get_selected()

        assert model.get_value(selected, GridPlugin.NAME) == "Enabled"
        assert model.get_value(selected, GridPlugin.ACTIVE) is True
        assert subject.settings_button.get_sensitive() is False
        detail = "<b>Enabled</b> (1.0.0)\n<small>Description</small>"
        assert model.get_value(selected, GridPlugin.DETAIL) == detail

    def test_selects_plugin(self, subject, plugin_manager, disabled_plugin):
        plugin_manager.appendPluginToCategory(disabled_plugin, self.CATEGORY)
        subject.refresh()

        selection = subject.plugin_list.get_selection()
        selection.select_path("0")

        model, selected = selection.get_selected()
        assert model.get_value(selected, GridPlugin.NAME) == "Disabled"
        assert model.get_value(selected, GridPlugin.ACTIVE) is False
        assert subject.settings_button.get_sensitive() is False

    def test_open_plugin_settings(self, subject, plugin_manager, disabled_plugin):
        plugin_manager.appendPluginToCategory(disabled_plugin, "Default")
        toplevel = Gtk.Label()
        subject.set_toplevel(toplevel)
        subject.refresh()

        subject.settings_button.emit("clicked")

        disabled_plugin.plugin_object.open_settings.assert_called_once_with(toplevel)

    Scenario = namedtuple("Scenario", "plugin name active settings")

    @pytest.mark.parametrize(
        "scenario",
        [
            Scenario("enabled_plugin", "Enabled", False, False),
            Scenario("disabled_plugin", "Disabled", True, True),
        ],
    )
    def test_enables_configurable_plugin(
        self,
        scenario: Scenario,
        subject,
        plugin_manager,
        enabled_plugin,
        disabled_plugin,
    ):
        plugin_manager.appendPluginToCategory(locals()[scenario.plugin], self.CATEGORY)
        subject.refresh()

        path = Gtk.TreePath.new_from_string("0")
        subject._on_row_toggled(None, path)

        selection = subject.plugin_list.get_selection()
        model, selected = selection.get_selected()
        assert model.get_value(selected, GridPlugin.NAME) == scenario.name
        assert model.get_value(selected, GridPlugin.ACTIVE) is scenario.active
        assert subject.settings_button.get_sensitive() is scenario.settings


class TestPreference:
    SPEC = "tomate.ui.preference"

    @pytest.fixture
    def mock_extension_tab(self, mocker):
        return mocker.Mock(widget=Gtk.Label())

    @pytest.fixture
    def mock_timer_tab(self, mocker):
        return mocker.Mock(widget=Gtk.Label())

    @pytest.fixture
    def subject(self, graph, plugin_manager, mock_config, mock_proxy):
        graph.register_instance("tomate.plugin", plugin_manager)
        graph.register_instance("tomate.config", mock_config)
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
    Scenario = namedtuple("Scenario", "option duration attr")

    @pytest.fixture
    def subject(self, graph, mock_config):
        config = {
            ("Timer", "pomodoro_duration"): 24,
            ("Timer", "longbreak_duration"): 14,
            ("Timer", "shortbreak_duration"): 4,
        }
        set_config(mock_config, "get_int", config)

        graph.register_instance("tomate.config", mock_config)
        scan_to_graph([PACKAGE], graph)
        return graph.get(self.SPEC)

    def test_module(self, graph, subject):
        instance = graph.get(self.SPEC)

        assert isinstance(instance, TimerTab)
        assert instance is subject

    @pytest.mark.parametrize(
        "scenario",
        [
            Scenario("pomodoro_duration", 24, "pomodoro"),
            Scenario("longbreak_duration", 14, "longbreak"),
            Scenario("shortbreak_duration", 4, "shortbreak"),
        ],
    )
    def test_save_config_when_pomodoro_duration_value_changes(
        self, scenario: Scenario, mock_config, subject
    ):
        option = getattr(subject, scenario.attr)
        option.emit("value-changed")

        refresh_gui()

        mock_config.set.assert_called_once_with(
            "Timer", scenario.option, str(scenario.duration)
        )
