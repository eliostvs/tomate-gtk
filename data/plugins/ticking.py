import logging

import gi
from wiring import Graph

gi.require_version("Gst", "1.0")

import tomate.pomodoro.plugin as plugin
from tomate.audio import GStreamerPlayer
from tomate.pomodoro import (
    Bus,
    Events,
    SessionPayload,
    SessionType,
    on,
    suppress_errors,
)

logger = logging.getLogger(__name__)


class TickingPlugin(plugin.Plugin):
    has_settings = False
    SECTION_NAME = "ticking_plugin"

    @suppress_errors
    def __init__(self):
        super().__init__()
        self.config = None
        self.player = None
        self.session = None

    def configure(self, bus: Bus, graph: Graph) -> None:
        super().configure(bus, graph)
        self.config = graph.get("tomate.config")
        self.session = graph.get("tomate.session")

    @suppress_errors
    def activate(self) -> None:
        super().activate()
        logger.debug("action=activate uri=%s volume=%f", self.audio_path, self.volume)
        self.player = GStreamerPlayer(repeat=True)
        self.player.file = self.audio_path
        self.player.volume = self.volume

        if self.session.is_running() and self.session.current == SessionType.POMODORO:
            self.player.play()

    @suppress_errors
    def deactivate(self) -> None:
        super().deactivate()
        logger.debug("action=deactivate")

        if self.player:
            self.player.stop()

    @suppress_errors
    @on(Events.SESSION_START)
    def on_start(self, payload: SessionPayload) -> None:
        logger.debug(f"action=play session_type={payload.type}")
        if self.player and payload.type == SessionType.POMODORO:
            self.player.play()

    @suppress_errors
    @on(Events.SESSION_INTERRUPT, Events.SESSION_END)
    def on_end(self, **_) -> None:
        logger.debug("action=stop")
        if self.player:
            self.player.stop()

    @property
    def audio_path(self) -> str:
        return self.config.get(self.SECTION_NAME, "uri", fallback=self.config.media_uri("clock.ogg"))

    @property
    def volume(self) -> float:
        return self.config.get_float(self.SECTION_NAME, "volume", fallback=1.0)
