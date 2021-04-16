import os

import pytest
from gi.repository import Gtk
from wiring import Graph

from tomate.pomodoro import Bus, Config, PluginEngine, Session
from tomate.ui import ShortcutEngine, Window

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture
def session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def bus() -> Bus:
    return Bus()


@pytest.fixture
def graph() -> Graph:
    g = Graph()
    g.register_instance(Graph, g)
    return g


@pytest.fixture
def window(mocker):
    return mocker.Mock(spec=Window, widget=Gtk.Window())


@pytest.fixture
def config(bus, tmpdir) -> Config:
    cfg = Config(bus)
    tmp_path = tmpdir.mkdir("tomate").join("tomate.config")
    cfg.config_path = lambda: tmp_path.strpath
    return cfg


@pytest.fixture
def shortcut_engine(config: Config) -> ShortcutEngine:
    return ShortcutEngine(config)


@pytest.fixture
def plugin_engine(bus: Bus, graph: Graph, config: Config) -> PluginEngine:
    return PluginEngine(bus, config, graph)
