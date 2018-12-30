from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.dialogs.about import AboutDialog


def test_about_module(graph, config):
    scan_to_graph(['tomate_gtk.dialogs.about'], graph)

    assert 'view.about' in graph.providers

    provider = graph.providers['view.about']
    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.about'), AboutDialog)
