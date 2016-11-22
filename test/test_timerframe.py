from __future__ import unicode_literals

from wiring import SingletonScope

from tomate_gtk.widgets.timerframe import TimerFrame


def test_timerframe_module(graph):
    assert 'view.timerframe' in graph.providers

    provider = graph.providers['view.timerframe']

    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.timerframe'), TimerFrame)
