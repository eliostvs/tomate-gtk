import os

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro.event import Events, on
from tomate.pomodoro.graph import graph
from tomate.pomodoro.plugin import Plugin, PluginManager, suppress_errors


def test_module(config):
    graph.providers.clear()
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.pomodoro.plugin"], graph)

    instance = graph.get("tomate.plugin")

    assert isinstance(instance, PluginManager)
    assert instance == graph.get("tomate.plugin")


class Subject(Plugin):
    @on(Events.SESSION_CHANGE)
    def bar(self, sender):
        return sender


def test_connects_events_when_plugin_activate(bus):
    graph.providers.clear()
    graph.register_instance("tomate.bus", bus)
    plugin = Subject()
    plugin.activate()

    result = bus.send(Events.SESSION_CHANGE)

    assert result == [(plugin.bar, Events.SESSION_CHANGE)]


def test_disconnects_events_when_plugin_deactivate(bus):
    graph.providers.clear()
    graph.register_instance("tomate.bus", bus)
    plugin = Subject()
    plugin.activate()
    plugin.deactivate()

    result = bus.send(Events.SESSION_CHANGE)

    assert result == []


def test_does_not_raise_exception_when_debug_is_disabled():
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
