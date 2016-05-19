from __future__ import unicode_literals

from gi.repository import Gtk
from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.appmenu import Appmenu, AppmenuModule


def test_module():
    assert list(AppmenuModule.providers.keys()) == ['view.appmenu']

    AppmenuModule().add_to(graph)

    provider = graph.providers['view.appmenu']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope

    assert provider.dependencies == {'menu': 'view.menu'}

    menu = Mock(widget=Gtk.Menu())

    graph.register_instance('view.menu', menu)

    assert isinstance(graph.get('view.appmenu'), Appmenu)
