from __future__ import unicode_literals

import logging

from gi.repository import Gtk

from wiring import Module, SingletonScope

from tomate.signals import subscribe
from tomate.utils import format_time_left

logger = logging.getLogger(__name__)


class TimerFrame(Gtk.Frame):

    subscriptions = (
        ('session_ended', 'update_session'),
        ('sessions_reseted', 'update_session'),
        ('session_interrupted', 'update_timer'),
        ('task_changed', 'update_timer'),
        ('timer_updated', 'update_timer'),
    )

    @subscribe
    def __init__(self):
        Gtk.Frame.__init__(
            self,
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

        self.add(box)

        self.update_session(0)

    def update_timer(self, *args, **kwargs):
        time_left = format_time_left(kwargs.get('time_left', 25 * 60))

        markup = '<span font="60">{}</span>'.format(time_left)
        self.timer_label.set_markup(markup)

        logger.debug('timer label update %s', time_left)

    def update_session(self, *args, **kwargs):
        sessions = kwargs.get('sessions', 0)

        markup = ('<span font="12">{0} pomodoros</span>'
                  .format(sessions))

        self.sessions_label.set_markup(markup)

        logger.debug('session label update %s', sessions)


class TimerFrameProvider(Module):
    factories = {
        'view.timerframe': (TimerFrame, SingletonScope)
    }
