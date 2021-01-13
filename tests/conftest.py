import os
import time
from typing import Dict, Tuple, Any

import pytest
from blinker import Namespace
from gi.repository import Gtk, GLib
from wiring import Graph
from wiring.scanning import scan_to_graph

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture()
def mock_config(mocker, monkeypatch):
    from tomate.pomodoro.config import Config

    icon_path = os.path.join(TEST_DATA_DIR, "tomate", "media", "tomate.png")
    return mocker.Mock(
        Config,
        SECTION_SHORTCUTS=Config.SECTION_SHORTCUTS,
        SECTION_TIMER=Config.SECTION_TIMER,
        parser=mocker.Mock(),
        **{"get_int.return_value": 25, "icon_path.return_value": icon_path}
    )


def set_config(mock, method: str, config: Dict[Tuple, Any]):
    """
    Easy way to configure the return value based on the mocked method params.
    """

    def side_effect(*args, **kwargs):
        keys = list(args)

        if kwargs is not None:
            keys.extend(kwargs.keys())

        return config[tuple(keys)]

    getattr(mock, method).side_effect = side_effect


@pytest.fixture()
def mock_session(mocker):
    from tomate.pomodoro.session import Session

    return mocker.Mock(spec=Session)


@pytest.fixture()
def dispatcher():
    return Namespace().signal("dispatcher")


@pytest.fixture()
def mock_timer(mocker):
    from tomate.pomodoro.timer import Timer

    return mocker.Mock(Timer)


@pytest.fixture()
def graph():
    return Graph()


@pytest.fixture()
def mock_view(mocker):
    return mocker.Mock(widget=mocker.Mock(Gtk.Window))


@pytest.fixture
def mock_proxy(mocker, mock_view):
    from tomate.pomodoro.proxy import lazy_proxy

    return mocker.Mock(
        lazy_proxy,
        side_effect=lambda spec: mock_view if spec == "tomate.ui.view" else None,
    )


def refresh_gui(delay: int = 0) -> None:
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    time.sleep(delay)


def run_loop_for(seconds: int = 1) -> None:
    GLib.timeout_add_seconds(seconds, Gtk.main_quit)
    Gtk.main()


@pytest.fixture
def mock_shortcut(mocker):
    from tomate.ui.shortcut import ShortcutManager

    instance = mocker.Mock(ShortcutManager)

    instance.label.side_effect = lambda name, fallback: name

    return instance


@pytest.fixture()
def real_config(graph, dispatcher, monkeypatch):
    monkeypatch.setenv("XDG_DATA_DIRS", TEST_DATA_DIR)
    monkeypatch.setenv("XDG_DATA_HOME", TEST_DATA_DIR)
    monkeypatch.setenv("XDG_CONFIG_HOME", TEST_DATA_DIR)

    graph.register_instance("tomate.events.config", dispatcher)
    scan_to_graph(["tomate.pomodoro.config"], graph)
    return graph.get("tomate.config")


@pytest.fixture()
def real_shortcut(graph, real_config):
    graph.register_instance("tomate.config", real_config)
    scan_to_graph(["tomate.ui.shortcut"], graph)
    return graph.get("tomate.ui.shortcut")


def assert_shortcut_called(shortcut_manager, shortcut, want=True):
    window = Gtk.Window()
    shortcut_manager.initialize(window)
    key, mod = Gtk.accelerator_parse(shortcut)
    assert Gtk.accel_groups_activate(window, key, mod) is want
