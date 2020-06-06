import pytest
from wiring import Graph
from wiring.scanning import scan_to_graph


@pytest.fixture()
def subject(graph):
    graph.register_instance(Graph, graph)
    scan_to_graph(["tomate.pomodoro.proxy"], graph)
    return graph.get("tomate.proxy")


def test_lazy_proxy(graph, subject):
    graph.register_instance("foo", {"a": 1, "b": 2})
    proxy = subject("foo")

    assert sorted(proxy.keys()) == ["a", "b"]
    assert sorted(proxy.values()) == [1, 2]
