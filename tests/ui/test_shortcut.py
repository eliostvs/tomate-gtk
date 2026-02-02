import pytest
from gi.repository import Gio, Gtk
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


def test_connect(shortcut_engine, mocker, gtk_app):
    callback = mocker.Mock()
    shortcut = Shortcut("start", "<control>s")
    window = Gtk.ApplicationWindow(application=gtk_app)

    action_group = Gio.SimpleActionGroup()
    action = Gio.SimpleAction.new("start", None)
    action.connect("activate", lambda *_: callback())
    action_group.add_action(action)
    window.insert_action_group("win", action_group)

    shortcut_engine.connect(shortcut, "win.start")
    assert active_shortcut(shortcut_engine, shortcut, window=window) is True

    callback.assert_called_once_with()


def test_disconnect(shortcut_engine):
    shortcut = Shortcut("start", "<control>s")
    shortcut_engine.connect(shortcut, "win.start")

    shortcut_engine.disconnect(shortcut)

    assert active_shortcut(shortcut_engine, shortcut) is False


def test_change(shortcut_engine):
    old_shortcut = Shortcut("start", "<control>a")
    new_shortcut = Shortcut("start", "<control>b")

    shortcut_engine.connect(old_shortcut, "win.start")
    shortcut_engine.change(new_shortcut)

    assert shortcut_engine.action_name(new_shortcut) == "win.start"
    assert shortcut_engine.action_name(old_shortcut) == "win.start"
