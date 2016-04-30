from __future__ import unicode_literals

from gi.repository import Gtk
from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.appmenu import Appmenu
from tomate_gtk.widgets.toolbar import Toolbar, ToolbarModule


def setup_module():
    graph.register_instance('tomate.menu', Gtk.Menu())
    graph.register_instance('view.menu', Mock(widget=Gtk.Menu()))
    graph.register_instance('tomate.session', Mock())
    graph.register_factory('view.appmenu', Appmenu)

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
