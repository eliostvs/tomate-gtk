from __future__ import unicode_literals

import pytest
import os
from mock import Mock
from wiring.scanning import scan_to_graph


@pytest.fixture
def graph():
    from tomate.graph import graph

    scan_to_graph(['tomate', 'tomate_gtk'], graph)

    return graph


@pytest.fixture
def config():
    parent = os.path.dirname(os.path.dirname(__file__))
    icon_path = os.path.join(parent, 'data/icons/hicolor/16x16/apps/tomate-plugin.png')
    return Mock(**{'get_int.return_value': 25, 'get_icon_path.return_value': icon_path})


@pytest.fixture
def plugin_manager():
    return Mock()


@pytest.fixture
def lazy_proxy():
    return Mock()
