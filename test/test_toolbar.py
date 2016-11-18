from __future__ import unicode_literals

from gi.repository import Gtk
from mock import Mock

from tomate_gtk.widgets.appmenu import Appmenu
from tomate_gtk.widgets.toolbar import Toolbar


def test_toolbar_module(graph):
    assert 'view.toolbar' in graph.providers

    graph.register_instance('tomate.menu', Gtk.Menu())
    graph.register_instance('view.menu', Mock(widget=Gtk.Menu()))
    graph.register_instance('tomate.session', Mock())
    graph.register_factory('view.appmenu', Appmenu)

    provider = graph.providers['view.toolbar']

    assert provider.dependencies == {'session': 'tomate.session',
                                     'appmenu': 'view.appmenu'}

    toolbar = graph.get('view.toolbar')

    assert isinstance(toolbar, Toolbar)
