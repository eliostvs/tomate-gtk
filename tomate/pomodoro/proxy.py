from wiring import injected, Graph
from wiring.scanning import register


class LazyProxy(object):
    def __init__(self, spec, graph):
        self._spec = spec
        self._graph = graph

    def __getattr__(self, attr):
        target = self._graph.get(self._spec)
        return getattr(target, attr)


@register.function("tomate.proxy")
def lazy_proxy(spec, graph=injected(Graph)):
    return LazyProxy(spec, graph)
