import os
import time

import pytest
from gi.repository import Gtk
from wiring import Graph


@pytest.fixture()
def mock_config(mocker):
    from tomate.pomodoro.config import Config

    parent_directory = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(
        parent_directory, "data/icons/hicolor/16x16/apps/tomate-plugin.png"
    )
    instance = mocker.Mock(
        Config,
        SECTION_SHORTCUTS=Config.SECTION_SHORTCUTS,
        SECTION_TIMER=Config.SECTION_TIMER,
        parser=mocker.Mock(),
        **{"get_int.return_value": 25, "get_icon_path.return_value": icon_path}
    )

    return instance


@pytest.fixture()
def mock_session(mocker):
    from tomate.pomodoro.session import Session

    return mocker.Mock(Session)


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


def refresh_gui(delay=0):
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    time.sleep(delay)


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
