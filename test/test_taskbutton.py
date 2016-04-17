from __future__ import unicode_literals


from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.taskbutton import TaskButton, TaskButtonModule


def test_module():
    assert TaskButtonModule.providers.keys() == ['view.taskbutton']

    TaskButtonModule().add_to(graph)
    provider = graph.providers['view.taskbutton']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope
    assert provider.dependencies == {'session': 'tomate.session'}

    graph.register_factory('tomate.session', Mock)

    assert isinstance(graph.get('view.taskbutton'), TaskButton)
