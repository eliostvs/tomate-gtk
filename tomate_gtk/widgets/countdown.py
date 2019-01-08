import logging

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Subscriber, Events, on
from tomate.utils import format_time_left
from wiring import SingletonScope
from wiring.scanning import register

logger = logging.getLogger(__name__)


@register.factory("view.countdown", scope=SingletonScope)
class Countdown(Subscriber):
    def __init__(self):
        self.widget = Gtk.Label(margin_top=30, margin_bottom=10, margin_right=10, margin_left=10)

    @on(Events.Timer, [State.changed])
    def on_timer_changed(self, sender=None, **kwargs):
        self._update_text(kwargs.get("time_left"))

    @on(Events.Session, [State.stopped, State.changed])
    def on_session_stop_or_changed(self, sender=None, **kwargs):
        self._update_text(kwargs.get("duration"))

    def _update_text(self, value):
        formatted_value = format_time_left(value)

        self.widget.set_markup(self.timer_markup(formatted_value))

        logger.debug(
            "component=timerFrame action=updateFrame value=%s", formatted_value
        )

    @staticmethod
    def timer_markup(time_left):
        return '<span face="sans-serif" font="45">{}</span>'.format(time_left)
