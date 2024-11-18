import logging

import gi

import tomate.pomodoro.plugin as plugin
from tomate.pomodoro import Events, on, suppress_errors

gi.require_version("Playerctl", "2.0")

from gi.repository import GLib, Playerctl

logger = logging.getLogger(__name__)


class AutoPausePlugin(plugin.Plugin):
    @suppress_errors
    @on(Events.SESSION_END)
    def on_session_end(self, **_):
        self.pause()

    def pause(self) -> None:
        try:
            for player in Playerctl.list_players():
                instance = Playerctl.Player.new_for_source(player.instance, player.source)
                logger.debug(
                    "action=check player=%s status=%s",
                    player.name,
                    instance.props.playback_status,
                )

                # pause is not an idempotent operation, it can start a paused player :(
                # so we need to check if the player is running first
                if instance.props.playback_status == Playerctl.PlaybackStatus.PLAYING:
                    instance.pause()
                    logger.debug("action=paused player=%s", player.name)

        except GLib.Error as err:
            logger.error("action=failed error='%s'", err)
