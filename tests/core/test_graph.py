from wiring import Graph
from wiring.scanning import scan_to_graph


def test_returns_graph_instance():
    package = "tomate.core.graph"

    graph = Graph()

    scan_to_graph([package], graph)

    assert Graph in graph.providers
