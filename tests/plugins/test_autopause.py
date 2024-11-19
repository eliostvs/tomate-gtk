import gi
import pytest

gi.require_version("Playerctl", "2.0")
gi.require_version("Gtk", "3.0")

from tomate.pomodoro import Events
from tomate.ui.testing import create_session_payload


@pytest.fixture
def plugin(bus, graph):
    from autopause import AutoPausePlugin

    instance = AutoPausePlugin()
    instance.configure(bus, graph)
    return instance


def test_stop_all_running_players(bus, plugin, mocker):
    from gi.repository import Playerctl

    playing = mocker.Mock(props=mocker.Mock(playback_status=Playerctl.PlaybackStatus.PLAYING))
    paused = mocker.Mock(props=mocker.Mock(playback_status=Playerctl.PlaybackStatus.PAUSED))
    players = {
        "playing-playing": playing,
        "paused-paused": paused,
    }

    def side_effect(instance, source):
        return players.get(f"{instance}-{source}")

    mocker.patch(
        "autopause.Playerctl.list_players",
        return_value=[
            mocker.Mock(instance="playing", source="playing"),
            mocker.Mock(instance="paused", source="paused"),
        ],
    )
    mocker.patch("autopause.Playerctl.Player.new_for_source", side_effect)

    plugin.activate()

    bus.send(Events.SESSION_END, payload=create_session_payload())

    paused.pause.assert_not_called()
    playing.pause.assert_called_once()
