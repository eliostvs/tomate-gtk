from __future__ import unicode_literals

from mock import Mock
from tomate.config import Config
from wiring import SingletonScope

from tomate_gtk.dialogs.about import AboutDialog


def test_module(graph):
    assert 'view.about' in graph.providers

    provider = graph.providers['view.about']
    assert provider.scope == SingletonScope

    graph.register_factory('tomate.events', Mock)
    graph.register_factory('config.parser', Mock)
    graph.register_factory('tomate.config', Config)

    assert isinstance(graph.get('view.about'), AboutDialog)
