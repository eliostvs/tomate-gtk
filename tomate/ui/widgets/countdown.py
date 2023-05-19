import logging
from typing import Union

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import (Bus, Events, SessionPayload, Subscriber,
                             TimerPayload, on)

logger = logging.getLogger(__name__)


@register.factory("tomate.ui.countdown", scope=SingletonScope)
class Countdown(Subscriber):
    @inject(bus="tomate.bus")
    def __init__(self, bus: Bus):
        self.widget = Gtk.Label(margin_top=30, margin_bottom=10, margin_right=10, margin_left=10, label="00:00")
        self.connect(bus)

    @on(Events.TIMER_UPDATE, Events.SESSION_READY, Events.SESSION_INTERRUPT, Events.SESSION_CHANGE)
    def _update_countdown(self, payload: Union[SessionPayload, TimerPayload]) -> None:
        logger.debug("action=update countdown=%s", payload.countdown)
        self.widget.set_markup(self.timer_markup(payload.countdown))

    @staticmethod
    def timer_markup(time_left: str) -> str:
        return '<span face="sans-serif" font="45">{}</span>'.format(time_left)
