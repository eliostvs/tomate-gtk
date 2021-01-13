import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph


@pytest.fixture
def subject(graph, dispatcher):
    from tomate.pomodoro.config import Config
    graph.register_instance("tomate.config", Config(dispatcher))
    scan_to_graph(["tomate.ui.shortcut"], graph)
    return graph.get("tomate.ui.shortcut")


def test_label(subject):
    label = subject.label("start", "")

    assert label == "Ctrl+S"


def test_label_with_fallback(subject):
    label = subject.label("stop", "<control>p")

    assert label == "Ctrl+P"


def test_connect(subject, mocker):
    window = Gtk.Window()
    subject.initialize(window)

    callback = mocker.Mock()
    subject.connect("start", callback, "")

    assert_shortcut_called(subject.accel_group, window, "<control>s", callback)


def test_change(subject, mock_config, mocker):
    window = Gtk.Window()
    subject.initialize(window)
    new_shortcut = "<control>b"
    option = "start"
    callback = mocker.Mock()

    subject.connect(option, callback, "")
    subject.change(option, new_shortcut)

    assert_shortcut_called(subject.accel_group, window, new_shortcut, callback)


def test_module(graph, subject):
    from tomate.ui.shortcut import ShortcutManager

    instance = graph.get("tomate.ui.shortcut")

    assert isinstance(instance, ShortcutManager)
    assert instance is subject


def assert_shortcut_called(accel_group, window, shortcut, callback):
    key, mod = Gtk.accelerator_parse(shortcut)
    result = Gtk.accel_groups_activate(window, key, mod)

    assert result is True
    callback.assert_called_once_with(accel_group, window, key, mod)
