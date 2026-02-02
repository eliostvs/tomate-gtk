import os

import gi
import pytest
from wiring import Graph

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk

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
def gtk_app():
    return Gtk.Application(application_id="com.github.Tomate.Test")


@pytest.fixture
def window(mocker, gtk_app):
    return mocker.Mock(spec=Window, widget=Gtk.ApplicationWindow(application=gtk_app))


@pytest.fixture
def toplevel(gtk_app):
    return Gtk.ApplicationWindow(application=gtk_app)


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
