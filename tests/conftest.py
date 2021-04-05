import os
import time

import pytest
from gi.repository import Gtk
from wiring import Graph

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture()
def session(mocker):
    from tomate.pomodoro.session import Session

    return mocker.Mock(spec=Session)


@pytest.fixture()
def bus():
    from tomate.pomodoro.event import Bus

    Bus.receivers.clear()
    return Bus


@pytest.fixture()
def graph():
    g = Graph()
    g.register_instance(Graph, g)
    return g


@pytest.fixture()
def view(mocker):
    return mocker.Mock(widget=mocker.Mock(Gtk.Window))


def refresh_gui(delay: int = 0) -> None:
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    time.sleep(delay)


@pytest.fixture()
def config(bus, tmpdir):
    from tomate.pomodoro.config import Config

    instance = Config(bus)
    tmp_path = tmpdir.mkdir("tomate").join("tomate.config")
    instance.config_path = lambda: tmp_path.strpath
    return instance


@pytest.fixture()
def shortcut_manager(config):
    from tomate.ui.shortcut import ShortcutManager

    return ShortcutManager(config)


def assert_shortcut_called(shortcut_manager, shortcut, want=True, window=None):
    if window is None:
        window = Gtk.Window()

    shortcut_manager.init(window)
    key, mod = Gtk.accelerator_parse(shortcut)
    assert Gtk.accel_groups_activate(window, key, mod) is want


def create_session_end_payload(**kwargs):
    from tomate.pomodoro.session import EndPayload, Type

    defaults = {
        "id": "1234",
        "duration": 5 * 60,
        "pomodoros": 1,
        "type": Type.SHORT_BREAK,
    }
    defaults.update(kwargs)
    return EndPayload(**defaults)


def create_session_payload(**kwargs):
    from tomate.pomodoro.session import Payload, Type

    defaults = {
        "id": "1234",
        "duration": 25 * 60,
        "pomodoros": 0,
        "type": Type.POMODORO,
    }
    defaults.update(kwargs)
    return Payload(**defaults)
