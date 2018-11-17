import locale
import logging
from locale import gettext as _

from wiring import inject, SingletonScope
from wiring.scanning import register

from tomate.constant import Task, State
from tomate.event import Subscriber, on, Events
from .mode_button import ModeButton

locale.textdomain('tomate')
logger = logging.getLogger(__name__)


@register.factory('view.taskbutton', scope=SingletonScope)
class TaskButton(Subscriber):
    @inject(session='tomate.session')
    def __init__(self, session):
        self.session = session

        self.mode_button = ModeButton(
            can_focus=False,
            homogeneous=True,
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
        )

        self.mode_button.append_text(_('Pomodoro'))
        self.mode_button.append_text(_('Short Break'))
        self.mode_button.append_text(_('Long Break'))
        self.mode_button.set_selected(Task.pomodoro)

        self.mode_button.connect('mode_changed', self.on_mode_changed)

    def on_mode_changed(self, widget, index):
        task = Task.by_index(index)
        self.session.change_task(task=task)

    @on(Events.Session, [State.finished])
    def change_selected(self, sender=None, **kwargs):
        task = kwargs.get('task', Task.pomodoro)

        logger.debug('component=taskButton action=changeSelected session=%s', task)

        self.mode_button.set_selected(task.value)

    @on(Events.Session, [State.started])
    def disable(self, sender=None, **kwargs):
        self.mode_button.set_sensitive(False)

    @on(Events.Session, [State.finished, State.stopped])
    def enable(self, sender=None, **kwargs):
        self.mode_button.set_sensitive(True)

    @property
    def widget(self):
        return self.mode_button
