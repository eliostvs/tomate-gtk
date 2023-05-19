import logging

import gi

gi.require_version("Gst", "1.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gst

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GStreamerPlayer:
    def __init__(self, repeat=False):
        Gst.init(None)
        self.repeat = repeat
        self._file = None
        self._is_about_to_finished = False

        self._playbin = Gst.ElementFactory.make("playbin", "player")
        self._volume_filter = Gst.ElementFactory.make("volume", "volume")
        self._playbin.props.audio_filter = self._volume_filter
        self._playbin.bus.add_signal_watch()
        self._playbin.bus.connect("message", self._on_bus_callback)
        self._playbin.connect("about-to-finish", self._on_about_to_finish)
        self._playbin.volume = 1.0
        self._volume_filter.volume = 0

    @property
    def file(self) -> str:
        return self._file

    @file.setter
    def file(self, filepath: str) -> None:
        _, state, pending_state = self._playbin.get_state(Gst.CLOCK_TIME_NONE)
        self._file = filepath

        logger.debug(f"action=set_file filepath={filepath} state={state} pending_state={pending_state}")

        if not self._file:
            self.stop()
            return

        if pending_state != Gst.State.VOID_PENDING:
            state = pending_state

        if state == Gst.State.PLAYING or state == Gst.State.PAUSED:
            self._is_about_to_finished = False
            self._playbin.set_state(Gst.State.READY)
            self._playbin.props.uri = self._file
            self._playbin.set_state(state)

    @property
    def volume(self) -> float:
        return self._volume_filter.props.volume

    @volume.setter
    def volume(self, volume: float) -> None:
        logger.debug(f"action=set_volume volume={volume}")
        self._volume_filter.props.volume = max(0.0, min(1.0, volume))

    def play(self) -> None:
        logger.debug("action=play")
        self._playbin.props.uri = self._file
        self._playbin.set_state(Gst.State.PLAYING)

    def stop(self) -> None:
        logger.debug("action=stop")
        self._playbin.set_state(Gst.State.NULL)

    def _on_bus_callback(self, _, message):
        if message.type == Gst.MessageType.EOS:
            if self._is_about_to_finished:
                self._is_about_to_finished = False
            else:
                self._finished()

        elif message.type == Gst.MessageType.ERROR:
            logger.error("action=audio_failed message='%s-%s'", *message.parse_error())
            self.stop()

    def _on_about_to_finish(self, _) -> None:
        logger.debug("action=about_to_finish")
        self._is_about_to_finished = True
        self._finished()

    def _finished(self) -> None:
        current_uri = self._playbin.props.current_uri

        logger.debug(f"action=finished repeat={self.repeat} current_uri={current_uri}")

        if current_uri and self.repeat:
            self._playbin.props.uri = current_uri
