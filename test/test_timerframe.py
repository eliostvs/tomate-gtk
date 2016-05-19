from __future__ import unicode_literals

from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.widgets.timerframe import TimerFrame, TimerFrameModule


def test_timeframe_module():

    TimerFrameModule.providers.keys() == ['view.timerframe']

    TimerFrameModule().add_to(graph)

    provider = graph.providers['view.timerframe']

    assert isinstance(provider, FactoryProvider)
    assert SingletonScope == provider.scope
    assert provider.dependencies == {}
    assert isinstance(graph.get('view.timerframe'), TimerFrame)
