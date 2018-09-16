import logging

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Subscriber, Events, on
from tomate.utils import format_time_left
from wiring import SingletonScope, inject
from wiring.scanning import register

DEFAULT_TIME_LEFT = 25 * 60

logger = logging.getLogger(__name__)


@register.factory('view.timerframe', scope=SingletonScope)
class TimerFrame(Subscriber):
    @inject(task_entry='view.taskentry')
    def __init__(self, task_entry):
        self.task_entry = task_entry

        self.timer_label = Gtk.Label(margin_bottom=14)

        self.widget = Gtk.Box(
            margin_left=12,
            margin_right=12,
            orientation=Gtk.Orientation.VERTICAL,
        )

        self.widget.pack_start(self.timer_label, False, False, 0)
        self.widget.pack_start(self.task_entry.widget, False, False, 0)

    @on(Events.Timer, [State.changed])
    @on(Events.Session, [State.stopped, State.changed])
    def update_timer(self, sender=None, **kwargs):
        time_left = kwargs.get('time_left', DEFAULT_TIME_LEFT)

        self.timer_label.set_markup(self.time_left_markup(time_left))

        logger.debug('timer label update %s', time_left)

    @staticmethod
    def time_left_markup(time_left):
        markup = '<span font="60">{}</span>'.format(format_time_left(time_left))
        return markup
