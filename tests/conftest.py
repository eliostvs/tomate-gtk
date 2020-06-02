import os
import time

import pytest
from blinker import Namespace
from gi.repository import Gtk, GLib
from wiring import Graph


@pytest.fixture()
def mock_config(mocker):
    from tomate.pomodoro.config import Config

    parent_directory = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(
        parent_directory, "data/icons/hicolor/16x16/apps/tomate-plugin.png"
    )
    return mocker.Mock(
        Config,
        SECTION_SHORTCUTS=Config.SECTION_SHORTCUTS,
        SECTION_TIMER=Config.SECTION_TIMER,
        parser=mocker.Mock(),
        **{"get_int.return_value": 25, "get_icon_path.return_value": icon_path}
    )


@pytest.fixture()
def mock_session(mocker):
    from tomate.pomodoro.session import Session

    return mocker.Mock(Session)


@pytest.fixture()
def timer_dispatcher():
    return Namespace().signal('timer')


@pytest.fixture()
def session_dispatcher():
    return Namespace().signal('session')


@pytest.fixture()
def mock_timer(mocker):
    from tomate.pomodoro.timer import Timer

    return mocker.Mock(Timer)


@pytest.fixture()
def graph():
    return Graph()


@pytest.fixture()
def mock_plugin(mocker):
    from yapsy.PluginManager import PluginManager

    return mocker.Mock(PluginManager)


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
def mock_shortcuts(mocker):
    from tomate.ui.shortcut import ShortcutManager

    instance = mocker.Mock(
        ShortcutManager,
        START=ShortcutManager.START,
        STOP=ShortcutManager.STOP,
        RESET=ShortcutManager.RESET,
    )

    instance.label.side_effect = lambda name: name

    return instance
