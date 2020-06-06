import os
import time
from typing import Dict, Tuple, Any

import pytest
from blinker import Namespace
from gi.repository import Gtk, GLib
from wiring import Graph

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

    instance = mocker.Mock(
        ShortcutManager,
        START=ShortcutManager.START,
        STOP=ShortcutManager.STOP,
        RESET=ShortcutManager.RESET,
    )

    instance.label.side_effect = lambda name: name

    return instance
