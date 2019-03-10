import pytest
from gi.repository import Gtk
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.ui.dialogs import ExtensionTab, PreferenceDialog, TimerTab

PACKAGE = "tomate.ui.dialogs.preference"


def setup_plugin_manager(plugin_manager, plugin):
    plugin_manager.getAllPlugins.return_value = [plugin]
    plugin_manager.getPluginByName.side_effect = (
        lambda name: plugin if name == plugin.name else None
    )


def describe_extension_tab():
    @pytest.fixture
    def plugin(mocker):
        plug = mocker.Mock(version="1.1.1", description="description")
        plug.name = "plugin"
        return plug

    @pytest.fixture
    def subject(mock_plugin, mock_config, mock_proxy, plugin):
        setup_plugin_manager(mock_plugin, plugin)

        return ExtensionTab(mock_plugin, mock_config, mock_proxy)

    def test_refresh_search_for_plugins(subject, mock_plugin):
        # when
        subject.refresh()

        # then
        mock_plugin.getAllPlugins.assert_called_once()

    def test_disable_settings_button_when_plugin_when_has_no_settings(subject, plugin):
        # given
        plugin.plugin_object.is_activated = True
        plugin.plugin_object.has_activated = False

        # when
        subject.refresh()

        refresh_gui(0)

        # then
        assert subject._settings_button.get_sensitive() is False

    def test_enable_settings_button_when_plugin_has_settings(subject, plugin):
        # given
        plugin.plugin_object.is_activated = True
        plugin.plugin_object.has_settings = True

        # when
        subject.refresh()

        refresh_gui(0)

        # then
        assert subject._settings_button.get_sensitive() is True

    def test_show_plugin_settings(subject, plugin, mock_view):
        # given
        plugin.plugin_object.is_activated = True
        plugin.plugin_object.has_settings = True
        subject._preference_dialog = mock_view

        # when
        subject.refresh()
        subject._settings_button.emit("clicked")

        refresh_gui(0)

        # then
        plugin.plugin_object.settings_window.return_value.set_transient_for(
            mock_view.widget
        )
        plugin.plugin_object.settings_window.return_value.run.assert_called_once_with()

    def test_module(graph, mock_session, mock_config, mock_plugin, mock_proxy):
        specification = "tomate.ui.preference.extension"

        scan_to_graph([PACKAGE], graph)

        graph.register_instance("tomate.plugin", mock_plugin)
        graph.register_instance("tomate.config", mock_config)
        graph.register_instance("tomate.proxy", mock_proxy)

        assert specification in graph.providers

        provider = graph.providers[specification]

        assert provider.scope == SingletonScope
        assert isinstance(graph.get(specification), ExtensionTab)


def describe_preference_dialog():
    @pytest.fixture
    def mock_extension_tab(mocker):
        return mocker.Mock(spec=ExtensionTab, widget=Gtk.Label())

    @pytest.fixture
    def mock_timer_tab(mocker):
        return mocker.Mock(spec=TimerTab, widget=Gtk.Label())

    @pytest.fixture
    def subject(mock_timer_tab, mock_extension_tab, mocker):
        mocker.patch("tomate.ui.dialogs.preference.Gtk.Dialog")
        mocker.patch("tomate.ui.dialogs.preference.Gtk.Stack")
        mocker.patch("tomate.ui.dialogs.preference.Gtk.StackSwitcher")
        mocker.patch("tomate.ui.dialogs.preference.Gtk.Box")

        return PreferenceDialog(mock_timer_tab, mock_extension_tab)

    def test_refresh_plugins_on_start(subject, mock_extension_tab):
        # given
        from tomate.ui.dialogs.preference import Gtk

        gtk_dialog = Gtk.Dialog.return_value

        # when
        subject.run()

        # then
        mock_extension_tab.refresh.assert_called_once()
        gtk_dialog.run.assert_called_once_with()

    def test_select_timer_tab_on_start(subject):
        # given
        from tomate.ui.dialogs.preference import Gtk

        gtk_stack = Gtk.Stack.return_value

        # then
        gtk_stack.set_visible_child_name.assert_called_once_with("timer")

    def test_module(graph, mock_config, mock_proxy, mock_plugin):
        specification = "tomate.ui.preference"

        scan_to_graph([PACKAGE], graph)

        graph.register_instance("tomate.plugin", mock_plugin)
        graph.register_instance("tomate.config", mock_config)
        graph.register_instance("tomate.proxy", mock_proxy)

        assert specification in graph.providers

        provider = graph.providers[specification]

        assert provider.scope == SingletonScope

        assert isinstance(graph.get(specification), PreferenceDialog)


def setup_config(config, option, value):
    def side_effect(section, opt):
        if section == "Timer" and opt == option:
            return value

    config.get_int.side_effect = side_effect


def describe_timer_tab():
    @pytest.fixture
    def subject(mock_config):
        return TimerTab(mock_config)

    def test_save_config_when_pomodoro_duration_value_changes(mock_config, subject):
        # given
        setup_config(mock_config, "pomodoro_duration", 25)

        # when
        subject.pomodoro_duration.set_value(25)
        subject.pomodoro_duration.emit("value-changed")

        refresh_gui(0)

        # then
        mock_config.set.assert_called_once_with("Timer", "pomodoro_duration", "25")

    def test_save_config_when_short_break_duration_changes(mock_config, subject):
        # given
        setup_config(mock_config, "shortbreak_duration", 5)

        # when
        subject.shortbreak_duration.set_value(5)
        subject.shortbreak_duration.emit("value-changed")

        refresh_gui(0)

        # then
        mock_config.set.assert_called_with("Timer", "shortbreak_duration", "5")

    def test_save_config_when_long_break_duration_changes(mock_config, subject):
        # given
        setup_config(mock_config, "longbreak_duration", 15)

        # when
        subject.longbreak_duration.set_value(15)
        subject.longbreak_duration.emit("value-changed")

        refresh_gui(0)

        # then
        mock_config.set.assert_called_with("Timer", "longbreak_duration", "15")

    def test_module(graph, mock_config):
        specification = "tomate.ui.preference.timer"

        scan_to_graph([PACKAGE], graph)

        assert specification in graph.providers

        graph.register_instance("tomate.config", mock_config)

        provider = graph.providers[specification]

        assert provider.scope == SingletonScope
        assert isinstance(graph.get(specification), TimerTab)
