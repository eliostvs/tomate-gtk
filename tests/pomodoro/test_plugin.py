import os

import pytest
from wiring.scanning import scan_to_graph

from tests.conftest import EVENT_ID, EVENT_OCCURRED_AT, deliver_events
from tomate.pomodoro import Event, Events, Plugin, PluginEngine, on, suppress_errors


class ExpectedError(Exception):
    pass


@pytest.fixture
def plugin_engine(bus, graph, config) -> PluginEngine:
    config.plugin_paths = lambda: [os.path.join(os.path.dirname(__file__), "..", "data", "tomate", "plugins")]
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

    def test_activate(self, _bus, plugin_engine):
        plugin_engine.collect()
        plugin_a = plugin_engine.lookup("PluginA")

        assert plugin_a.is_activated is False

        plugin_engine.activate("PluginA")
        assert plugin_a.is_activated is True

    def test_deactivate(self, _bus, plugin_engine):
        plugin_engine.collect()
        plugin_b = plugin_engine.lookup("PluginB")

        assert plugin_b.is_activated is True

        plugin_engine.deactivate("PluginB")
        assert plugin_b.is_activated is False

    def test_deactivation_skips_a_queued_typed_event(self, bus, plugin_engine):
        plugin_engine.collect()
        plugin_b = plugin_engine.lookup("PluginB")

        event = bus.publish(Events.WINDOW_SHOW)
        plugin_engine.deactivate("PluginB")
        deliver_events()

        assert not hasattr(plugin_b.plugin_object, "last_event")
        assert event.type is Events.WINDOW_SHOW

    def test_active_plugin_receives_deferred_event_metadata(self, bus, plugin_engine):
        plugin_engine.collect()
        plugin_b = plugin_engine.lookup("PluginB")

        event = bus.publish(Events.WINDOW_SHOW)

        assert not hasattr(plugin_b.plugin_object, "last_event")
        deliver_events()

        assert plugin_b.plugin_object.last_event is event
        assert event.id == EVENT_ID
        assert event.occurred_at == EVENT_OCCURRED_AT
        assert event.type is Events.WINDOW_SHOW
        assert event.payload is None

    def test_failing_plugin_does_not_block_later_plugin(self, bus, graph):
        class FailingPlugin(Plugin):
            @on(Events.WINDOW_SHOW)
            def receive(self, _event: Event[None]):
                raise ValueError("broken plugin")

        class ReceivingPlugin(Plugin):
            @on(Events.WINDOW_SHOW)
            def receive(self, event: Event[None]):
                self.event = event

        failing = FailingPlugin()
        receiving = ReceivingPlugin()
        failing.configure(bus, graph)
        receiving.configure(bus, graph)
        failing.activate()
        receiving.activate()

        event = bus.publish(Events.WINDOW_SHOW)
        deliver_events()

        assert receiving.event is event

    def test_all(self, plugin_engine):
        plugin_engine.collect()

        got = [(p.name, str(p.version), p.is_activated, p.plugin_object.has_settings) for p in plugin_engine.all()]

        assert got == [
            ("PluginA", "1.0", False, True),
            ("PluginB", "2.0", True, False),
        ]

    def test_lookup(self, plugin_engine):
        plugin_engine.collect()

        assert plugin_engine.lookup("Not Exist") is None

        plugin = plugin_engine.lookup("PluginA")

        assert plugin is not None


class TestRaiseException:
    def test_does_not_raise_exception_when_debug_is_disabled(self):
        os.unsetenv("TOMATE_DEBUG")

        @suppress_errors
        def raise_exception():
            raise ExpectedError()

        assert not raise_exception()

    def test_raises_exception_when_debug_enable(self):
        os.environ.setdefault("TOMATE_DEBUG", "1")

        @suppress_errors
        def raise_exception():
            raise ExpectedError()

        with pytest.raises(ExpectedError):
            raise_exception()
