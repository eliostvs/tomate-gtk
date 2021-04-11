import os

import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import TEST_DATA_DIR
from tomate.pomodoro import Config, ConfigPayload, Events


@pytest.fixture
def config(graph, bus):
    graph.register_instance("tomate.bus", bus)
    scan_to_graph(["tomate.pomodoro.config"], graph)
    return graph.get("tomate.config")


def test_module(graph, config):
    instance = graph.get("tomate.config")

    assert isinstance(instance, Config)
    assert instance is config


def test_get_plugin_paths(config):
    expected = os.path.join(TEST_DATA_DIR, "tomate", "plugins")

    assert expected in config.plugin_paths()


def test_get_config_path(config):
    assert config.config_path() == os.path.join(TEST_DATA_DIR, "tomate", "tomate.conf")


def test_get_media_uri_raises_error_when_media_is_not_found(config):
    with pytest.raises(OSError) as excinfo:
        config.media_uri("tomate.jpg")

    assert str(excinfo.value) == "Resource 'tomate.jpg' not found!"


def test_get_media_uri(config):
    expected = "file://" + os.path.join(TEST_DATA_DIR, "tomate", "media", "tomate.png")

    assert config.media_uri("tomate.png") == expected


def test_get_icon_path_raises_when_icon_not_found(config):
    with pytest.raises(OSError) as excinfo:
        assert config.icon_path("foo", 48, "foobar")

    assert str(excinfo.value) == "Icon 'foo' not found!"


def test_set_option(config, tmpdir, bus, mocker):
    config_path = tmpdir.mkdir("tmp").join("tomate.config").strpath
    config.config_path = lambda: config_path

    subscriber = mocker.Mock()
    bus.connect(Events.CONFIG_CHANGE, subscriber, weak=False)

    config.set("section", "option", "value")

    assert config.get("section", "option") == "value"
    payload = ConfigPayload("set", "section", "option", "value")
    subscriber.assert_called_once_with(Events.CONFIG_CHANGE, payload=payload)


def test_get_icon_path(config):
    expected = os.path.join(TEST_DATA_DIR, "icons", "hicolor", "24x24", "apps", "tomate.png")
    assert config.icon_path("tomate", 48, "hicolor") == expected


def test_icon_paths(config):
    assert os.path.join(TEST_DATA_DIR, "icons") in config.icon_paths()


def test_get_option_as_int(config):
    assert config.get_int("Timer", "pomodoro_duration") == 25


def test_get_option(config):
    assert config.get("Timer", "pomodoro_duration") == "25"


def test_get_option_with_fallback(config):
    assert config.get("Timer", "pomodoro_pass", fallback="23") == "23"


def test_get_defaults_option(config):
    assert config.get("Timer", "shortbreak_duration") == "5"


def test_remove_section(config, tmpdir):
    tmp_path = tmpdir.mkdir("tmp").join("tomate.config")
    config.config_path = lambda: tmp_path.strpath

    config.set("section", "option", "value")
    config.remove("section", "option")

    assert config.parser.has_option("section", "option") is False
