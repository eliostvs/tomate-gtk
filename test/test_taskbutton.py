from __future__ import unicode_literals

from mock import Mock
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.widgets.taskbutton import TaskButton


def test_taskbutton_module(graph):
    scan_to_graph(['tomate_gtk.widgets.taskbutton'], graph)

    assert 'view.taskbutton' in graph.providers

    provider = graph.providers['view.taskbutton']

    assert provider.scope == SingletonScope

    graph.register_factory('tomate.session', Mock)

    assert isinstance(graph.get('view.taskbutton'), TaskButton)
