import os

import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import TEST_DATA_DIR


@pytest.fixture()
def subject(graph, dispatcher, monkeypatch):
    monkeypatch.setenv("XDG_DATA_DIRS", TEST_DATA_DIR)
    monkeypatch.setenv("XDG_DATA_HOME", TEST_DATA_DIR)
    monkeypatch.setenv("XDG_CONFIG_HOME", TEST_DATA_DIR)

    graph.register_instance("tomate.events.config", dispatcher)
    scan_to_graph(["tomate.pomodoro.config"], graph)

    return graph.get("tomate.config")


def test_module(graph, subject):
    from tomate.pomodoro.config import Config

    instance = graph.get("tomate.config")

    assert isinstance(instance, Config)
    assert instance is subject


def test_get_plugin_paths(subject):
    assert subject.plugin_paths() == [os.path.join(TEST_DATA_DIR, "tomate", "plugins")]


def test_get_config_path(subject):
    assert subject.config_path() == os.path.join(TEST_DATA_DIR, "tomate", "tomate.conf")


def test_get_media_uri_raises_error_when_media_is_not_found(subject):
    with pytest.raises(OSError) as excinfo:
        subject.media_uri("tomate.jpg")

    assert str(excinfo.value) == "Resource 'tomate.jpg' not found!"


def test_get_media_uri(subject):
    expected = "file://" + os.path.join(TEST_DATA_DIR, "tomate", "media", "tomate.png")

    assert subject.media_uri("tomate.png") == expected


def test_get_icon_path_raises_when_icon_not_found(subject):
    with pytest.raises(OSError) as excinfo:
        assert subject.icon_path("foo", 48, "foobar")

    assert str(excinfo.value) == "Icon 'foo' not found!"


def test_set_option(subject, tmpdir, monkeypatch):
    config = tmpdir.mkdir("tmp").join("tomate.config")
    subject.config_path = lambda: config.strpath

    subject.set("section", "option", "value")

    text = "[section]\noption = value"
    assert text in config.read()


def test_get_icon_path(subject):
    expected = os.path.join(
        TEST_DATA_DIR, "icons", "hicolor", "22x22", "apps", "tomate.png"
    )
    assert subject.icon_path("tomate", 48, "hicolor") == expected


def test_icon_paths(subject):
    assert subject.icon_paths() == [os.path.join(TEST_DATA_DIR, "icons")]


def test_get_option_as_int(subject):
    assert subject.get_int("Timer", "pomodoro_duration") == 24


def test_get_option(subject):
    assert subject.get("Timer", "pomodoro_duration") == "24"


def test_get_option_with_fallback(subject):
    assert subject.get("Timer", "pomodoro_pass", fallback="23") == "23"


def test_get_defaults_option(subject):
    assert subject.get("Timer", "shortbreak_duration") == "5"
