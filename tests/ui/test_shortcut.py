import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tomate.ui import Shortcut, ShortcutEngine
from tomate.ui.testing import active_shortcut


@pytest.fixture
def shortcut_engine(bus, config, graph) -> ShortcutEngine:
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.ui.shortcut"], graph)
    return graph.get("tomate.ui.shortcut")


def test_module(graph, shortcut_engine):
    instance = graph.get("tomate.ui.shortcut")

    assert isinstance(instance, ShortcutEngine)
    assert instance is shortcut_engine


def test_label(shortcut_engine):
    label = shortcut_engine.label(Shortcut("test", ""))

    assert label == "Ctrl+S"


def test_label_with_fallback(shortcut_engine):
    label = shortcut_engine.label(Shortcut("", "<control>p"))

    assert label == "Ctrl+P"


def test_connect(shortcut_engine, mocker):
    callback = mocker.Mock(return_value=True)
    shortcut = Shortcut("start", "<control>s")

    shortcut_engine.connect(shortcut, callback)
    assert active_shortcut(shortcut_engine, shortcut) is True

    key, mod = Gtk.accelerator_parse(shortcut.value)
    callback.assert_called_once_with(shortcut_engine.accel_group, mocker.ANY, key, mod)


def test_disconnect(shortcut_engine, mocker):
    shortcut = Shortcut("start", "<control>s")
    shortcut_engine.connect(shortcut, mocker.Mock())

    shortcut_engine.disconnect(shortcut)

    assert active_shortcut(shortcut_engine, shortcut) is False


def test_change(shortcut_engine, mocker):
    callback = mocker.Mock(return_value=True)
    old_shortcut = Shortcut("start", "<control>a")
    new_shortcut = Shortcut("start", "<control>b")

    shortcut_engine.connect(old_shortcut, callback)
    shortcut_engine.change(new_shortcut)

    assert active_shortcut(shortcut_engine, old_shortcut) is False
    assert active_shortcut(shortcut_engine, new_shortcut) is True

    key, mod = Gtk.accelerator_parse(new_shortcut.value)
    callback.assert_called_once_with(shortcut_engine.accel_group, mocker.ANY, key, mod)
