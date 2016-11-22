from __future__ import unicode_literals

import pytest
from mock import Mock
from wiring.scanning import scan_to_graph


@pytest.fixture
def graph():
    from tomate.graph import graph

    scan_to_graph(['tomate', 'tomate_gtk'], graph)

    return graph


@pytest.fixture
def config():
    return Mock(**{'get_int.return_value': 25})
