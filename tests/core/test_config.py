import configparser
import os
from unittest.mock import Mock, mock_open, patch

import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.core.config import Config, SettingsPayload

BaseDirectory_attrs = {
    "xdg_config_home": "/home/mock/.config",
    "load_data_paths.side_effect": lambda *args: [os.path.join("/usr/mock/", *args)],
}


@pytest.fixture()
def subject():
    return Config(Mock(), Mock(configparser.RawConfigParser))


@patch("tomate.core.config.BaseDirectory", spec_set=True, **BaseDirectory_attrs)
class TestConfig:
    def test_get_config_path(self, base_directory, subject):
        assert subject.get_config_path() == "/home/mock/.config/tomate/tomate.conf"

    def test_get_plugin_path(self, base_directory, subject):
        assert subject.get_plugin_paths() == ["/usr/mock/tomate/plugins"]

    def test_write_config(self, base_directory, subject):
        mo = mock_open()

        with patch("tomate.core.config.open", mo, create=True):
            subject.save()

        subject.parser.write.assert_called_once_with(mo())

    @patch("tomate.core.config.os.path.exists", spec_set=True, return_value=True)
    def test_get_media_file(self, path, base_directory, subject):
        file_path = "file:///usr/mock/tomate/media/alarm.mp3"

        assert subject.get_media_uri("alarm.mp3") == file_path

    def test_get_resource_path_raise_exception(self, base_directory, subject):
        with pytest.raises(EnvironmentError):
            subject.get_resource_path("/file/not/exist/")

    @patch("tomate.core.config.IconTheme.getIconPath", return_value=None)
    def test_get_icon_path_raise_exception(
        self, get_icon_path, base_directory, subject
    ):
        with pytest.raises(EnvironmentError):
            subject.get_icon_path("tomate", 22)

    @patch("tomate.core.config.IconTheme.getIconPath", spec_set=True)
    def test_get_icon_path_success(self, get_icon_path, base_directory, subject):
        def side_effect(name, size, theme, extensions):
            return "/usr/mock/icons/hicolor/{size}x{size}/apps/{name}.png".format(
                name=name, size=size
            )

        get_icon_path.side_effect = side_effect

        expected_path = "/usr/mock/icons/hicolor/22x22/apps/tomate.png"

        assert subject.get_icon_path("tomate", 22) == expected_path

    def test_icon_paths_success(self, base_directory, subject):
        assert subject.get_icon_paths() == ["/usr/mock/icons"]

    def test_get_option(self, base_directory, subject):
        subject.get("section", "option")
        subject.parser.get.assert_called_with("section", "option", fallback=None)

    def test_get_in_option(self, base_directory, subject):
        subject.get_int("section", "option")
        subject.parser.getint.assert_called_with("section", "option", fallback=None)

    def test_get_option_using_defaults(self, based_directory):
        from tomate.core.config import Config, DEFAULTS

        config = Config(Mock(), configparser.RawConfigParser(defaults=DEFAULTS))

        assert int(DEFAULTS["pomodoro_duration"]) == config.get_int(
            "timer", "pomodoro_duration"
        )

    def test_set_option(self, base_directory, subject):
        subject.parser.has_section.return_value = False

        mo = mock_open()

        with patch("tomate.core.config.open", mo, create=True):
            subject.set("Timer", "Shortbreak Duration", 4)

            subject.parser.has_section.assert_called_once_with("timer")
            subject.parser.add_section.assert_called_once_with("timer")
            subject.parser.set.assert_called_once_with(
                "timer", "shortbreak_duration", 4
            )

            subject.parser.write.assert_called_once_with(mo())


@patch("tomate.core.config.BaseDirectory", spec_set=True, **BaseDirectory_attrs)
def test_emit_setting_changed(base_directory, subject):
    with patch("tomate.core.config.open", mock_open(), create=True):
        subject.set("Timer", "Pomodoro", 4)

        payload = SettingsPayload(
            section="timer", option="pomodoro", value=4, action="set"
        )

        subject._dispatcher.send.assert_called_once_with("timer", payload=payload)


def test_module(graph, mocker):
    spec = "tomate.config"
    package = "tomate.core.config"

    scan_to_graph([package], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    graph.register_factory("tomate.events.setting", mocker.Mock)

    assert isinstance(graph.get(spec), Config)
