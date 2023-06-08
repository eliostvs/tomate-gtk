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
        "playing": playing,
        "paused": paused,
    }

    def side_effect(player):
        return players.get(player.id)

    mocker.patch(
        "autopause.Playerctl.list_players",
        return_value=[mocker.Mock(id="playing"), mocker.Mock(id="paused")],
    )
    mocker.patch("autopause.Playerctl.Player.new_from_name", side_effect)

    plugin.activate()

    bus.send(Events.SESSION_END, payload=create_session_payload())

    paused.pause.assert_not_called()
    playing.pause.assert_called_once()
