import logging

from gi.repository import Gtk
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.constant import State
from tomate.event import Subscriber, Events, on
from tomate.utils import format_time_left

DEFAULT_TIME_LEFT = 25 * 60

logger = logging.getLogger(__name__)


@register.factory('view.timerframe', scope=SingletonScope)
class TimerFrame(Subscriber):
    @inject(taskentry='view.taskentry')
    def __init__(self, taskentry):
        self.task_entry = taskentry

        self.widget = Gtk.Frame(
            margin_bottom=2,
            margin_left=12,
            margin_right=12,
            margin_top=12,
            shadow_type=Gtk.ShadowType.IN,
        )

        self.timer_label = Gtk.Label(justify=Gtk.Justification.CENTER,
                                     expand=True,
                                     vexpand=True,
                                     halign=Gtk.Align.FILL,
                                     valign=Gtk.Align.FILL)

        box = Gtk.VBox()
        box.pack_start(self.timer_label, True, True, 0)
        box.pack_start(self.task_entry.widget, False, False, 0)

        self.widget.add(box)

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

