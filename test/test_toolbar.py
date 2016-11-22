from __future__ import unicode_literals

from gi.repository import Gtk
from mock import Mock
from wiring import SingletonScope

from tomate_gtk.widgets.appmenu import Appmenu
from tomate_gtk.widgets.toolbar import Toolbar


def test_toolbar_module(graph):
    assert 'view.toolbar' in graph.providers

    graph.register_instance('tomate.menu', Gtk.Menu())
    graph.register_instance('view.menu', Mock(widget=Gtk.Menu()))
    graph.register_instance('tomate.session', Mock())
    graph.register_factory('view.appmenu', Appmenu)

    provider = graph.providers['view.toolbar']
    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.toolbar'), Toolbar)
