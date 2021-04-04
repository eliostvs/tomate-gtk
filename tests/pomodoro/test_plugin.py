import os

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import State
from tomate.pomodoro.event import on
from tomate.pomodoro.plugin import PluginManager, Plugin, suppress_errors


@pytest.fixture()
def subject(graph, config):
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.pomodoro.plugin"], graph)
    return graph.get("tomate.plugin")


def test_module(graph, subject):
    instance = graph.get("tomate.plugin")

    assert isinstance(instance, PluginManager)
    assert instance is subject


@pytest.fixture()
def plugin(dispatcher):
    class Subject(Plugin):
        @on(dispatcher, [State.finished])
        def bar(self, sender):
            return sender

    return Subject()


def test_disconnect_events_when_plugin_deactivate(plugin, dispatcher):
    plugin.deactivate()

    result = dispatcher.send(State.finished)

    assert result == []


def test_connect_events_when_plugin_active(plugin, dispatcher):
    plugin.activate()

    result = dispatcher.send(State.finished)

    assert result == [(plugin.bar, State.finished)]


def test_doesnt_raise_exception_when_debug_is_disabled():
    os.environ.unsetenv("TOMATE_DEBUG")

    @suppress_errors
    def raise_exception():
        raise Exception()

    assert not raise_exception()


def test_raises_exception_when_debug_enable():
    os.environ.setdefault("TOMATE_DEBUG", "1")

    @suppress_errors
    def raise_exception():
        raise Exception()

    with pytest.raises(Exception):
        raise_exception()
