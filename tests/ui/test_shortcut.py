import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import set_config
from tomate.ui.shortcut import ShortcutManager


@pytest.fixture
def subject(graph, mock_config):
    graph.register_instance("tomate.config", mock_config)
    scan_to_graph(["tomate.ui.shortcut"], graph)
    return graph.get("tomate.ui.shortcut")


def test_label(subject, mock_config):
    set_config(mock_config, "get", {("shortcuts", "start", "fallback"): "<control>s"})

    label = subject.label("start")

    assert label == "Ctrl+S"


@pytest.mark.parametrize(
    "option,shortcut",
    (["start", "<control>s"], ["stop", "<control>p"], ["reset", "<control>r"]),
)
def test_connect(option, shortcut, subject, mocker, mock_config):
    window = Gtk.Window()
    subject.initialize(window)

    set_config(mock_config, "get", {("shortcuts", option, "fallback"): shortcut})

    callback = mocker.Mock()
    subject.connect(option, callback)

    key, mod = Gtk.accelerator_parse(shortcut)
    result = Gtk.accel_groups_activate(window, key, mod)

    assert result is True
    callback.assert_called_once_with(subject.accel_group, window, key, mod)


def test_change(subject, mock_config, mocker):
    window = Gtk.Window()
    subject.initialize(window)
    old = "<Control>b"
    new = "<Control>a"
    option = "start"
    set_config(mock_config, "get", {("shortcuts", option, "fallback"): old})

    subject.connect(option, mocker.Mock())
    subject.change(option, new)

    key, mod = Gtk.accelerator_parse(new)
    result = Gtk.accel_groups_activate(window, key, mod)

    assert result is True


def test_module(graph, subject):
    instance = graph.get("tomate.ui.shortcut")

    assert isinstance(instance, ShortcutManager)
    assert instance is subject
