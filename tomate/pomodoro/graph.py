from wiring import Graph
from wiring.scanning import register

graph = Graph()
register.instance(Graph)(graph)
