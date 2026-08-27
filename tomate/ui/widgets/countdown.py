import logging

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Bus, Event, Events, SessionPayload, TimerPayload

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.countdown", scope=SingletonScope)
class Countdown:
    @inject(bus="tomate.bus")
    def __init__(self, bus: Bus):
        self.widget = Gtk.Label(margin_top=30, margin_bottom=10, margin_right=10, margin_left=10, label="00:00")
        for event_type in (Events.TIMER_UPDATE, Events.SESSION_READY, Events.SESSION_INTERRUPT, Events.SESSION_CHANGE):
            bus.connect(event_type, self._update_countdown)

    def _update_countdown(self, event: Event[SessionPayload | TimerPayload]) -> None:
        payload = event.payload
        if payload is None:
            return
        logger.debug("action=update countdown=%s", payload.countdown)
        self.widget.set_markup(self.timer_markup(payload.countdown))

    @staticmethod
    def timer_markup(time_left: str) -> str:
        return f'<span face="sans-serif" font="45">{time_left}</span>'
