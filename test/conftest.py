from __future__ import unicode_literals

import pytest
from wiring.scanning import scan_to_graph


@pytest.fixture
def graph():
    from tomate.graph import graph

    scan_to_graph(['tomate', 'tomate_gtk'], graph)

    return graph
