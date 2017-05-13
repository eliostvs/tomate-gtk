from __future__ import unicode_literals

import os
import time

import pytest
from gi.repository import Gtk
from mock import Mock


@pytest.fixture
def graph():
    from tomate.graph import graph
    graph.providers.clear()

    return graph


@pytest.fixture
def config(graph):
    parent = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(parent, 'data/icons/hicolor/16x16/apps/tomate-plugin.png')
    mock_config = Mock(**{'get_int.return_value': 25, 'get_icon_path.return_value': icon_path})

    graph.register_instance('tomate.config', mock_config)

    return mock_config


@pytest.fixture
def plugin_manager(graph):
    mock_plugin_manager = Mock()
    graph.register_instance('tomate.plugin', mock_plugin_manager)
    return mock_plugin_manager


@pytest.fixture
def lazy_proxy(graph):
    mock_proxy = Mock()
    graph.register_instance('tomate.proxy', mock_proxy)
    return mock_proxy


def refresh_gui(delay=0):
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)
    time.sleep(delay)
