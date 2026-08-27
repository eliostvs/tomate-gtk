import os
from datetime import datetime, timezone
from uuid import UUID

import gi
import pytest
from wiring import Graph

gi.require_version("Gtk", "3.0")

from gi.repository import GLib, Gtk

from tomate.pomodoro import Bus, Config, PluginEngine, Session
from tomate.ui import ShortcutEngine, Window

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
EVENT_ID = UUID("12345678-1234-4abc-8def-123456789abc")
EVENT_OCCURRED_AT = datetime(2026, 8, 27, 12, 30, tzinfo=timezone.utc)


def deliver_events() -> None:
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)


def assert_received_event(subscriber, event_type, payload) -> None:
    subscriber.assert_called_once()
    event = subscriber.call_args.args[0]
    assert event.id == EVENT_ID
    assert event.occurred_at == EVENT_OCCURRED_AT
    assert event.type is event_type
    assert event.payload == payload


@pytest.fixture
def session(mocker):
    return mocker.Mock(spec=Session)


@pytest.fixture
def bus() -> Bus:
    return Bus(id_factory=lambda: EVENT_ID, clock=lambda: EVENT_OCCURRED_AT)


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
    config.plugin_paths = lambda: [os.path.join(TEST_DATA_DIR, "tomate", "plugins")]
    return PluginEngine(bus, config, graph)
