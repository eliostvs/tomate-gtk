import pytest
from gi.repository import Gtk

from tests.conftest import assert_shortcut_called


@pytest.fixture
def subject(shortcut_manager):
    return shortcut_manager


def test_label(subject):
    label = subject.label("start", "")

    assert label == "Ctrl+S"


def test_label_with_fallback(subject):
    label = subject.label("stop", "<control>p")

    assert label == "Ctrl+P"


def test_connect(subject, mocker):
    callback = mocker.Mock(return_value=True)
    subject.connect("start", callback)

    shortcut = "<control>s"
    assert_shortcut_called(subject, shortcut)

    key, mod = Gtk.accelerator_parse(shortcut)
    callback.assert_called_once_with(subject.accel_group, mocker.ANY, key, mod)


def test_disconnect(subject, mocker):
    shortcut = "<control>s"

    subject.connect("start", mocker.Mock(), fallback=shortcut)
    subject.disconnect("start", fallback=shortcut)

    assert_shortcut_called(subject, shortcut, want=False)


def test_change(subject, mocker):
    callback = mocker.Mock(return_value=True)
    name = "start"
    shortcut = "<control>b"

    subject.connect(name, callback)
    subject.change(name, shortcut)

    assert_shortcut_called(subject, shortcut)

    key, mod = Gtk.accelerator_parse(shortcut)
    callback.assert_called_once_with(subject.accel_group, mocker.ANY, key, mod)


def test_module(graph, subject):
    from tomate.ui.shortcut import ShortcutManager

    instance = graph.get("tomate.ui.shortcut")

    assert isinstance(instance, ShortcutManager)
    assert instance is subject
