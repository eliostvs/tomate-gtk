import os

import pytest
from yapsy.PluginInfo import PluginInfo

from tests.conftest import EVENT_ID, EVENT_OCCURRED_AT, deliver_events
from tomate.pomodoro import Event, Events, Plugin, PluginEngine, on, suppress_errors


class ExpectedError(Exception):
    pass


@pytest.fixture
def plugin_engine(bus, graph, config) -> PluginEngine:
    config.plugin_paths = lambda: [os.path.join(os.path.dirname(__file__), "..", "data", "tomate", "plugins")]
    return PluginEngine(bus, config, graph.resolve)


class TestPluginEngine:
    def test_collect(self, bus, plugin_engine):
        assert plugin_engine.has_plugins() is False

        plugin_engine.collect()

        assert plugin_engine.has_plugins() is True

        for plugin in plugin_engine.all():
            assert plugin.plugin_object.bus is bus
            assert plugin.plugin_object.resolve is plugin_engine._resolve

    def test_plugins_receive_no_graph_api(self, bus, config, graph):
        engine = PluginEngine(bus, config, graph.resolve)

        class InspectingPlugin(Plugin):
            pass

        plugin = InspectingPlugin()
        plugin_info = PluginInfo("Inspecting", "")
        plugin_info.plugin_object = plugin
        engine._configure_plugin(plugin_info)

        assert not hasattr(plugin.resolve, "register_instance")
        assert not hasattr(plugin.resolve, "register_factory")
        assert not hasattr(plugin.resolve, "clear")
        assert not hasattr(plugin.resolve, "providers")

    def test_activate(self, plugin_engine):
        plugin_engine.collect()
        plugin_a = plugin_engine.lookup("PluginA")

        assert plugin_a.is_activated is False

        plugin_engine.activate("PluginA")
        assert plugin_a.is_activated is True

    def test_deactivate(self, plugin_engine):
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
        failing.configure(bus, graph.resolve)
        receiving.configure(bus, graph.resolve)
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
