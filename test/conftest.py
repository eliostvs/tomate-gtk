import os
import time

import pytest
from gi.repository import Gtk


@pytest.fixture
def session(mocker):
    from tomate.session import Session

    return mocker.Mock(Session)


@pytest.fixture
def graph():
    from tomate.graph import graph

    graph.providers.clear()

    return graph


@pytest.fixture
def config(mocker):
    from tomate.config import Config

    parent_directory = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(
        parent_directory, "data/icons/hicolor/16x16/apps/tomate-plugin.png"
    )
    instance = mocker.Mock(
        Config,
        SECTION_SHORTCUTS=Config.SECTION_SHORTCUTS,
        SECTION_TIMER=Config.SECTION_TIMER,
        **{"get_int.return_value": 25, "get_icon_path.return_value": icon_path}
    )

    return instance


@pytest.fixture
def plugin_manager(mocker):
    return mocker.Mock()


@pytest.fixture
def lazy_proxy(mocker):
    from tomate.proxy import lazy_proxy

    return mocker.Mock(lazy_proxy)


def refresh_gui(delay=0):
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    time.sleep(delay)
