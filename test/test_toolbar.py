from __future__ import unicode_literals

from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope, Graph

from tomate_gtk.widgets.appmenu import Appmenu
from tomate_gtk.widgets.toolbar import Toolbar, ToolbarModule


def setup_module():
    graph.register_factory('view.preference', Mock)
    graph.register_factory('view.about', Mock)
    graph.register_factory('tomate.session', Mock)
    graph.register_factory('view.appmenu', Appmenu)
    graph.register_instance(Graph, graph)
    ToolbarModule().add_to(graph)


def test_toolbar_module():
    assert ['view.toolbar'] == ToolbarModule.providers.keys()

    provider = graph.providers['view.toolbar']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope

    assert provider.dependencies == {'session': 'tomate.session',
                                     'appmenu': 'view.appmenu'}

    toolbar = graph.get('view.toolbar')

    assert isinstance(toolbar, Toolbar)
