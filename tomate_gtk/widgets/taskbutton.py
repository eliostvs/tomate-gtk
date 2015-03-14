from __future__ import unicode_literals

import locale
import logging
from locale import gettext as _

from wiring import inject, Module, SingletonScope

from tomate.enums import Task
from tomate.signals import subscribe

from .modebutton import ModeButton

locale.textdomain('tomate')
logger = logging.getLogger(__name__)


class TaskButton(ModeButton):

    subscriptions = (
        ('session_started', 'disable'),
        ('session_interrupted', 'enable'),
        ('session_ended', 'change_selected'),
        ('session_ended', 'enable'),
    )

    @subscribe
    @inject(session='tomate.session')
    def __init__(self, session=None):
        self.session = session

        ModeButton.__init__(
            self,
            can_focus=False,
            homogeneous=True,
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
            margin_top=4,
            spacing=0,
        )

        self.append_text(_('Pomodoro'))
        self.append_text(_('Short Break'))
        self.append_text(_('Long Break'))
        self.set_selected(0)

        self.connect('mode_changed', self.on_mode_changed)

    def on_mode_changed(self, widget, index):
        task = Task.get_by_index(index)
        self.session.change_task(task=task)

    def change_selected(self, sender=None, **kwargs):
        task = kwargs.get('task', Task.pomodoro)

        logger.debug('task changed %s', task)

        self.set_selected(task.value)

    def disable(self, sender=None, **kwargs):
        self.set_sensitive(False)

    def enable(self, sender=None, **kwargs):
        self.set_sensitive(True)


class TaskButtonProvider(Module):

    factories = {
        'view.taskbutton': (TaskButton, SingletonScope)
    }
