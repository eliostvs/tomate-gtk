import os

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro.event import on
from tomate.pomodoro.plugin import Plugin, PluginManager, suppress_errors

TEST_EVENT = "TEST_EVENT"


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
def plugin(bus):
    class Subject(Plugin):
        @on(bus, [TEST_EVENT])
        def bar(self, sender):
            return sender

    return Subject()


def test_disconnects_events_when_plugin_deactivate(plugin, bus):
    plugin.deactivate()

    result = bus.send(TEST_EVENT)

    assert result == []


def test_connects_events_when_plugin_activate(plugin, bus):
    plugin.activate()

    result = bus.send(TEST_EVENT)

    assert result == [(plugin.bar, TEST_EVENT)]


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
