import logging

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Subscriber, Events, on
from tomate.utils import format_time_left
from wiring import SingletonScope
from wiring.scanning import register

logger = logging.getLogger(__name__)


@register.factory("view.timerframe", scope=SingletonScope)
class TimerFrame(Subscriber):
    DEFAULT_TIME_LEFT = 25 * 60

    def __init__(self):
        self.widget = Gtk.Label(margin_top=30)

    @on(Events.Timer, [State.changed])
    @on(Events.Session, [State.stopped, State.changed])
    def update_timer(self, sender=None, **kwargs):
        time_left = format_time_left(kwargs.get("time_left", self.DEFAULT_TIME_LEFT))

        self.widget.set_markup(self.time_left_markup(time_left))

        logger.debug("component=timerFrame action=updateTimer time_left=%s", time_left)

    @staticmethod
    def time_left_markup(time_left):
        return '<span face="sans-serif" font="50">{}</span>'.format(time_left)
