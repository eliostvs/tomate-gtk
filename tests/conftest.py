import os
import time

import pytest
from blinker import Namespace
from gi.repository import Gtk
from wiring import Graph
from wiring.scanning import scan_to_graph

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture()
def session(mocker):
    from tomate.pomodoro.session import Session

    return mocker.Mock(spec=Session)


@pytest.fixture()
def dispatcher():
    return Namespace().signal("dispatcher")


@pytest.fixture()
def graph():
    g = Graph()
    g.register_instance(Graph, g)
    return g


@pytest.fixture()
def mock_view(mocker):
    return mocker.Mock(widget=mocker.Mock(Gtk.Window))


def refresh_gui(delay: int = 0) -> None:
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    time.sleep(delay)


@pytest.fixture()
def real_config(graph, dispatcher, tmpdir):
    graph.register_instance("tomate.events.config", dispatcher)
    scan_to_graph(["tomate.pomodoro.config"], graph)

    instance = graph.get("tomate.config")
    tmp_path = tmpdir.mkdir("tomate").join("tomate.config")
    instance.config_path = lambda: tmp_path.strpath
    return instance


@pytest.fixture()
def shortcut_manager(graph, real_config):
    graph.register_instance("tomate.config", real_config)
    scan_to_graph(["tomate.ui.shortcut"], graph)
    return graph.get("tomate.ui.shortcut")


def assert_shortcut_called(shortcut_manager, shortcut, want=True, window=None):
    if window is None:
        window = Gtk.Window()

    shortcut_manager.initialize(window)
    key, mod = Gtk.accelerator_parse(shortcut)
    assert Gtk.accel_groups_activate(window, key, mod) is want
