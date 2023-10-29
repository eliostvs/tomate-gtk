from os.path import dirname, join
from unittest.mock import patch

import gi
import pytest

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")

from tomate.pomodoro import Events, SessionPayload, SessionType

DEFAULT_ALARM = f'file://{join(dirname(dirname(__file__)), "data", "tomate", "media", "clock.ogg")}'


@pytest.fixture
def plugin(bus, config, graph, session):
    graph.providers.clear()
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.config", config)
    graph.register_instance("tomate.session", session)

    from ticking import TickingPlugin

    instance = TickingPlugin()
    instance.configure(bus, graph)
    return instance


class TestPlugin:
    def test_loads_configuration_when_is_activated(self, bus, config, plugin):
        plugin.activate()

        assert plugin.player.volume == 0.5
        assert plugin.player.file == DEFAULT_ALARM
        assert plugin.player.repeat

    @patch("ticking.GStreamerPlayer")
    @pytest.mark.parametrize(
        "is_running,session_type,want",
        [
            (True, SessionType.POMODORO, True),
            (True, SessionType.SHORT_BREAK, False),
            (False, SessionType.POMODORO, False),
        ],
    )
    def test_starts_player_when_is_activated(
        self, player, is_running, session_type, want, bus, config, session, plugin
    ):
        session.is_running.return_value = is_running
        session.current = session_type

        plugin.activate()

        assert player.return_value.play.called == want

    @patch("ticking.GStreamerPlayer")
    def test_starts_player_when_session_start(self, player, bus, config, plugin):
        plugin.activate()

        bus.send(Events.SESSION_START, payload=create_session_payload())

        player.return_value.play.assert_called_once()

    @patch("ticking.GStreamerPlayer")
    @pytest.mark.parametrize("event", [Events.SESSION_END, Events.SESSION_INTERRUPT])
    def test_stops_player_when_session_(self, player, event, bus, config, plugin):
        plugin.activate()

        bus.send(Events.SESSION_START, payload=create_session_payload())
        bus.send(event)

        player.return_value.stop.assert_called_once()

    @patch("ticking.GStreamerPlayer")
    def test_stops_player_when_is_deactivate(self, player, bus, config, plugin):
        plugin.activate()

        plugin.deactivate()

        player.return_value.stop.assert_called_once()


def create_session_payload(**kwargs) -> SessionPayload:
    defaults = {
        "duration": 25 * 60,
        "pomodoros": 0,
        "type": SessionType.POMODORO,
    }
    defaults.update(kwargs)
    return SessionPayload(**defaults)
