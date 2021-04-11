import logging

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Events, SessionPayload, Subscriber, TimerPayload, format_time_left, on

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.countdown", scope=SingletonScope)
class Countdown(Subscriber):
    @inject(bus="tomate.bus")
    def __init__(self, bus: Bus):
        self.widget = Gtk.Label(margin_top=30, margin_bottom=10, margin_right=10, margin_left=10)
        self.connect(bus)

    @on(Events.TIMER_UPDATE)
    def _on_timer_update(self, _, payload: TimerPayload) -> None:
        self._update(payload.time_left)

    @on(Events.SESSION_INTERRUPT, Events.SESSION_CHANGE)
    def _on_session_change(self, _, payload: SessionPayload) -> None:
        self._update(payload.duration)

    def _update(self, duration: int) -> None:
        formatted_duration = format_time_left(duration)
        self.widget.set_markup(self.timer_markup(formatted_duration))
        logger.debug("action=update value=%s", formatted_duration)

    @staticmethod
    def timer_markup(time_left: str) -> str:
        return '<span face="sans-serif" font="45">{}</span>'.format(time_left)
