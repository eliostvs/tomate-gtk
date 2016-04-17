from __future__ import unicode_literals

from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope, Graph

from tomate_gtk.widgets.appmenu import Appmenu, AppmenuModule


def test_module():
    assert AppmenuModule.providers.keys() == ['view.appmenu']

    AppmenuModule().add_to(graph)

    provider = graph.providers['view.appmenu']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope

    assert provider.dependencies == {'about': 'view.about',
                                     'preference': 'view.preference',
                                     'graph': Graph}

    graph.register_factory('view.preference', Mock)
    graph.register_factory('view.about', Mock)

    assert isinstance(graph.get('view.appmenu'), Appmenu)
