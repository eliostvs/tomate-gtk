from __future__ import unicode_literals

import logging

from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Subscriber, Session, Timer, on
from tomate.utils import format_time_left
from wiring.scanning import register

logger = logging.getLogger(__name__)


@register.factory('view.timerframe')
class TimerFrame(Subscriber):
    def __init__(self):
        self.widget = Gtk.Frame(
            margin_bottom=2,
            margin_left=12,
            margin_right=12,
            margin_top=12,
            shadow_type=Gtk.ShadowType.IN,
        )

        self.timer_label = Gtk.Label(justify=Gtk.Justification.CENTER,
                                     hexpand=True,
                                     vexpand=True,
                                     halign=Gtk.Align.FILL,
                                     valign=Gtk.Align.FILL)

        self.sessions_label = Gtk.Label(justify=Gtk.Justification.CENTER,
                                        margin_bottom=12,
                                        hexpand=True)
        box = Gtk.VBox()
        box.pack_start(self.timer_label, True, True, 0)
        box.pack_start(self.sessions_label, False, False, 0)

        self.widget.add(box)

        self.update_session(0)

    @on(Timer, [State.changed])
    @on(Session, [State.stopped, State.changed])
    def update_timer(self, sender=None, **kwargs):
        time_left = format_time_left(kwargs.get('time_left', 25 * 60))

        markup = '<span font="60">{}</span>'.format(time_left)
        self.timer_label.set_markup(markup)

        logger.debug('timer label update %s', time_left)

    @on(Session, [State.changed, State.finished])
    def update_session(self, *args, **kwargs):
        sessions = kwargs.get('sessions', 0)

        markup = ('<span font="12">{0} pomodoros</span>'
                  .format(sessions))

        self.sessions_label.set_markup(markup)

        logger.debug('session label update %s', sessions)
