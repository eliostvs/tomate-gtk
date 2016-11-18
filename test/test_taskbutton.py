from __future__ import unicode_literals

from mock import Mock

from tomate_gtk.widgets.taskbutton import TaskButton


def test_taskbutton_module(graph):
    assert 'view.taskbutton' in graph.providers

    provider = graph.providers['view.taskbutton']

    assert provider.dependencies == {'session': 'tomate.session'}

    graph.register_factory('tomate.session', Mock)

    assert isinstance(graph.get('view.taskbutton'), TaskButton)
