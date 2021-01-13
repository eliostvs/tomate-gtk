import logging

from gi.repository import Gtk
from wiring import SingletonScope
from wiring.scanning import register

from tomate.pomodoro import State
from tomate.pomodoro.event import Subscriber, Events, on
from tomate.pomodoro.session import Payload as SessionPayload
from tomate.pomodoro.timer import Payload as TimerPayload, format_time_left

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.countdown", scope=SingletonScope)
class Countdown(Subscriber):
    def __init__(self):
        self.widget = Gtk.Label(margin_top=30, margin_bottom=10, margin_right=10, margin_left=10)

    @on(Events.Timer, [State.changed])
    def _on_timer_changed(self, _, payload: TimerPayload) -> None:
        self._update_text(payload.time_left)

    @on(Events.Session, [State.stopped, State.changed])
    def _on_session_stop_or_changed(self, _, payload: SessionPayload) -> None:
        self._update_text(payload.duration)

    def _update_text(self, value: int) -> None:
        formatted_value = format_time_left(value)
        self.widget.set_markup(self.timer_markup(formatted_value))

        logger.debug("action=update value=%s", formatted_value)

    @staticmethod
    def timer_markup(time_left: str) -> str:
        return '<span face="sans-serif" font="45">{}</span>'.format(time_left)
