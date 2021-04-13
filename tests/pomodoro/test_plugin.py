import os
from distutils.version import StrictVersion

import pytest
from wiring.scanning import scan_to_graph

from tomate.pomodoro import PluginEngine, suppress_errors


@pytest.fixture
def plugin_engine(config) -> PluginEngine:
    return PluginEngine(config)


def test_module(config, graph):
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.pomodoro.plugin"], graph)

    instance = graph.get("tomate.plugin")

    assert isinstance(instance, PluginEngine)
    assert instance == graph.get("tomate.plugin")


class TestPluginEngine:
    def test_collect(self, plugin_engine):
        assert plugin_engine.has_plugins() is False

        plugin_engine.collect()

        assert plugin_engine.has_plugins() is True

    def test_activate(self, plugin_engine):
        plugin_engine.collect()
        plugin_a = plugin_engine.lookup("PluginA")

        assert plugin_a.is_activated is False

        plugin_engine.activate("PluginA")
        assert plugin_a.is_activated is True

    def test_deactivate(self, plugin_engine):
        plugin_engine.collect()
        plugin_a = plugin_engine.lookup("PluginB")

        assert plugin_a.is_activated is True

        plugin_engine.deactivate("PluginB")
        assert plugin_a.is_activated is False

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
