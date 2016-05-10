from __future__ import unicode_literals

from mock import Mock
from tomate.config import Config
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.dialogs.about import AboutDialog, AboutDialogModule


def test_module():

    assert list(AboutDialogModule.providers.keys()) == ['view.about']

    AboutDialogModule().add_to(graph)

    provider = graph.providers['view.about']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope
    assert provider.dependencies == {'config': 'tomate.config'}

    graph.register_factory('tomate.events', Mock)
    graph.register_factory('config.parser', Mock)
    graph.register_factory('tomate.config', Config)

    assert isinstance(graph.get('view.about'), AboutDialog)
