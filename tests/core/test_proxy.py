from wiring.scanning import scan_to_graph

from tomate.core.proxy import LazyProxy, lazy_proxy


def test_lazy_proxy(graph):
    graph.register_instance("dict", {"a": 1, "b": 2})
    new_proxy = LazyProxy("dict", graph)

    assert sorted(new_proxy.keys()) == ["a", "b"]
    assert sorted(new_proxy.values()) == [1, 2]


def test_lazy_proxy_function(graph):
    new_proxy = lazy_proxy("foo", graph=graph)

    assert isinstance(new_proxy, LazyProxy)


def test_module(graph):
    spec = "tomate.proxy"

    scan_to_graph(["tomate.core.proxy"], graph)

    assert spec in graph.providers
