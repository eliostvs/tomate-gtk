import pytest
from conftest import refresh_gui
from gi.repository import Gtk, GLib
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.dialogs.preference import ExtensionTab, PreferenceDialog, TimerTab


@pytest.fixture
def extension_tab_mock(mocker):
    return mocker.Mock(spec=ExtensionTab, widget=Gtk.Button())


@pytest.fixture
def timer_tab(config):
    return TimerTab(config)


@pytest.fixture
def timer_tab_mock(mocker):
    return mocker.Mock(spec=TimerTab, widget=Gtk.Button())


@pytest.fixture
def preference(timer_tab_mock, extension_tab_mock):
    return PreferenceDialog(timer_tab_mock, extension_tab_mock)


class TestModule:
    def test_extension_tab(
            self, graph, session, config, plugin_manager, lazy_proxy
    ):
        graph.register_instance("tomate.plugin", plugin_manager)
        graph.register_instance("tomate.config", config)
        graph.register_instance("tomate.proxy", lazy_proxy)

        scan_to_graph(["tomate_gtk.dialogs.preference"], graph)

        assert "view.preference.extension" in graph.providers

        provider = graph.providers["view.preference.extension"]

        assert provider.scope == SingletonScope
        assert isinstance(graph.get("view.preference.extension"), ExtensionTab)

    def test_timer_tab(self, graph, config, session):
        graph.register_instance("tomate.config", config)

        scan_to_graph(["tomate_gtk.dialogs.preference"], graph)

        assert "view.preference.duration" in graph.providers

        provider = graph.providers["view.preference.duration"]

        assert provider.scope == SingletonScope
        assert isinstance(graph.get("view.preference.duration"), TimerTab)

    def test_preference(self, graph, config, lazy_proxy, plugin_manager):
        graph.register_instance("tomate.plugin", plugin_manager)
        graph.register_instance("tomate.config", config)
        graph.register_instance("tomate.proxy", lazy_proxy)

        scan_to_graph(["tomate_gtk.dialogs.preference"], graph)

        assert "view.preference" in graph.providers

        provider = graph.providers["view.preference"]

        assert provider.scope == SingletonScope

        assert isinstance(graph.get("view.preference"), PreferenceDialog)


@pytest.fixture
def plugin(mocker):
    plug = mocker.Mock(version="1.1.1", description="description")
    plug.name = "plugin"
    return plug


class TestPreferenceDialog:
    def test_refresh_plugin_list_when_widget_is_run(self, preference, extension_tab_mock):
        GLib.timeout_add(1, lambda: preference.destroy() and False)
        preference.run()

        extension_tab_mock.refresh.assert_called_once()

    def test_disable_plugin_settings_button_when_plugin_when_has_no_settings(
            self, plugin_manager, config, lazy_proxy, plugin
    ):
        plugin.plugin_object.is_activated = True
        plugin.plugin_object.has_activated = False
        self.setup_plugin_manager(plugin_manager, plugin)

        extension_tab = ExtensionTab(plugin_manager, config, lazy_proxy)
        extension_tab.refresh()
        refresh_gui(0)

        assert extension_tab.plugin_settings_button.get_sensitive() is False

    def test_activate_plugin_settings_button_when_plugin_has_settings(
            self, plugin_manager, config, lazy_proxy, plugin
    ):
        plugin.plugin_object.is_activated = True
        plugin.plugin_object.has_settings = True
        self.setup_plugin_manager(plugin_manager, plugin)

        extension_tab = ExtensionTab(plugin_manager, config, lazy_proxy)
        extension_tab.refresh()
        refresh_gui(0)

        assert extension_tab.plugin_settings_button.get_sensitive() is True

    def test_show_plugin_settings(
            self, plugin_manager, config, lazy_proxy, plugin, mocker
    ):
        plugin.plugin_object.is_activated = True
        plugin.plugin_object.has_settings = True
        self.setup_plugin_manager(plugin_manager, plugin)
        lazy_proxy.side_effect = (
            lambda name: mocker.Mock(widget="widget")
            if name == "view.preference"
            else None
        )

        extension_tab = ExtensionTab(plugin_manager, config, lazy_proxy)
        extension_tab.refresh()
        extension_tab.plugin_settings_button.emit("clicked")
        refresh_gui(0)

        plugin.plugin_object.settings_window.return_value.set_transient_for("widget")
        plugin.plugin_object.settings_window.return_value.run.assert_called_once_with()

    @staticmethod
    def setup_plugin_manager(plugin_manager, plugin):
        plugin_manager.getAllPlugins.return_value = [plugin]
        plugin_manager.getPluginByName.side_effect = (
            lambda name: plugin if name == plugin.name else None
        )

    def test_preference_widget(self, preference):
        assert preference.widget is preference


class TestTimerTab:
    def test_timer_tab_widget(self, timer_tab):
        assert timer_tab.widget is timer_tab

    def test_timer_tab_pomodoro_duration_changed(self, config, timer_tab):
        self.setup_config(config, "pomodoro_duration", 25)

        timer_tab.pomodoro_duration.set_value(25)
        timer_tab.pomodoro_duration.emit("value-changed")

        refresh_gui(0)

        config.set.assert_called_once_with("Timer", "pomodoro_duration", "25")

    def test_timer_tab_small_break_duration_changed(self, config, timer_tab):
        self.setup_config(config, "shortbreak_duration", 5)

        timer_tab.shortbreak_duration.set_value(5)
        timer_tab.shortbreak_duration.emit("value-changed")

        refresh_gui(0)

        config.set.assert_called_with("Timer", "shortbreak_duration", "5")

    def test_timer_tab_long_break_break_duration_changed(self, config, timer_tab):
        self.setup_config(config, "longbreak_duration", 15)

        timer_tab.longbreak_duration.set_value(15)
        timer_tab.longbreak_duration.emit("value-changed")

        refresh_gui(0)

        config.set.assert_called_with("Timer", "longbreak_duration", "15")

    @staticmethod
    def setup_config(config, option, value):
        def side_effect(section, opt):
            if section == "Timer" and opt == option:
                return value

        config.get_int.side_effect = side_effect
