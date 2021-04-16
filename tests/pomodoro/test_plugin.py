import os
from distutils.version import StrictVersion

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import Events, PluginEngine, suppress_errors


@pytest.fixture
def plugin_engine(bus, graph, config) -> PluginEngine:
    return PluginEngine(bus, config, graph)


def test_module(bus, config, graph):
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.pomodoro.plugin"], graph)

    instance = graph.get("tomate.plugin")

    assert isinstance(instance, PluginEngine)
    assert instance == graph.get("tomate.plugin")


class TestPluginEngine:
    def test_collect(self, bus, graph, plugin_engine):
        assert plugin_engine.has_plugins() is False

        plugin_engine.collect()

        assert plugin_engine.has_plugins() is True

        for plugin in plugin_engine.all():
            assert plugin.plugin_object.bus is bus
            assert plugin.plugin_object.graph is graph

    def test_activate(self, bus, plugin_engine):
        plugin_engine.collect()
        plugin_a = plugin_engine.lookup("PluginA")

        assert plugin_a.is_activated is False
        assert bus.is_connect(Events.WINDOW_SHOW, plugin_a.plugin_object.listener) is False

        plugin_engine.activate("PluginA")
        assert plugin_a.is_activated is True
        assert bus.is_connect(Events.WINDOW_SHOW, plugin_a.plugin_object.listener) is True

    def test_deactivate(self, bus, plugin_engine):
        plugin_engine.collect()
        plugin_b = plugin_engine.lookup("PluginB")

        assert plugin_b.is_activated is True
        assert bus.is_connect(Events.WINDOW_SHOW, plugin_b.plugin_object.listener) is True

        plugin_engine.deactivate("PluginB")
        assert plugin_b.is_activated is False
        assert bus.is_connect(Events.WINDOW_SHOW, plugin_b.plugin_object.listener) is False

    def test_all(self, plugin_engine):
        plugin_engine.collect()

        got = [(p.name, p.version, p.is_activated, p.plugin_object.has_settings) for p in plugin_engine.all()]

        assert got == [
            ("PluginA", StrictVersion("1.0.0"), False, True),
            ("PluginB", StrictVersion("2.0.0"), True, False),
        ]

    def test_lookup(self, plugin_engine):
        plugin_engine.collect()

        assert plugin_engine.lookup("Not Exist") is None

        plugin = plugin_engine.lookup("PluginA")

        assert plugin is not None


class TestRaiseException:
    def test_does_not_raise_exception_when_debug_is_disabled(self):
        os.environ.unsetenv("TOMATE_DEBUG")

        @suppress_errors
        def raise_exception():
            raise Exception()

        assert not raise_exception()

    def test_raises_exception_when_debug_enable(self):
        os.environ.setdefault("TOMATE_DEBUG", "1")

        @suppress_errors
        def raise_exception():
            raise Exception()

        with pytest.raises(Exception):
            raise_exception()
