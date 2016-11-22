from __future__ import unicode_literals

from gi.repository import Gtk
from mock import Mock
from wiring import SingletonScope

from tomate_gtk.widgets.appmenu import Appmenu


def test_module(graph):
    assert 'view.appmenu' in graph.providers

    provider = graph.providers['view.appmenu']

    assert provider.scope == SingletonScope

    graph.register_instance('view.menu', Mock(widget=Gtk.Menu()))

    assert isinstance(graph.get('view.appmenu'), Appmenu)
