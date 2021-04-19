from wiring import Graph
from wiring.scanning import scan_to_graph


def test_module():
    graph = Graph()

    scan_to_graph(["tomate.pomodoro.graph"], graph)

    assert isinstance(graph.get(Graph), Graph)
