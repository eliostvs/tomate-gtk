import logging

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Events, SessionPayload, Subscriber, TimerPayload, format_seconds, on

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.countdown", scope=SingletonScope)
class Countdown(Subscriber):
    @inject(bus="tomate.bus")
    def __init__(self, bus: Bus):
        self.widget = Gtk.Label(margin_top=30, margin_bottom=10, margin_right=10, margin_left=10)
        self.connect(bus)

    @on(Events.TIMER_UPDATE)
    def _on_timer_update(self, _, payload: TimerPayload) -> None:
        self._update(payload.format)

    @on(Events.SESSION_INTERRUPT, Events.SESSION_CHANGE)
    def _on_session_change(self, _, payload: SessionPayload) -> None:
        self._update(format_seconds(payload.duration))

    def _update(self, duration: str) -> None:
        self.widget.set_markup(self.timer_markup(duration))
        logger.debug("action=update duration=%s", duration)

    @staticmethod
    def timer_markup(time_left: str) -> str:
        return '<span face="sans-serif" font="45">{}</span>'.format(time_left)
