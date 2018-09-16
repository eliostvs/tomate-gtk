import locale
import logging
from locale import gettext as _

from wiring import inject, SingletonScope
from wiring.scanning import register

from tomate.constant import Task, State
from tomate.event import Subscriber, on, Events
from .modebutton import ModeButton

locale.textdomain('tomate')
logger = logging.getLogger(__name__)


@register.factory('view.taskbutton', scope=SingletonScope)
class TaskButton(Subscriber):
    @inject(session='tomate.session')
    def __init__(self, session):
        self.session = session

        self.modebutton = ModeButton(
            can_focus=False,
            homogeneous=True,
            margin_bottom=6,
            margin_left=12,
            margin_right=12,
            margin_top=0,
        )

        self.modebutton.append_text(_('Pomodoro'))
        self.modebutton.append_text(_('Short Break'))
        self.modebutton.append_text(_('Long Break'))
        self.modebutton.set_selected(Task.pomodoro)

        self.modebutton.connect('mode_changed', self.on_mode_changed)

    def on_mode_changed(self, widget, index):
        task = Task.by_index(index)
        self.session.change_task(task=task)

    @on(Events.Session, [State.finished])
    def change_selected(self, sender=None, **kwargs):
        task = kwargs.get('task', Task.pomodoro)

        logger.debug('task changed %s', task)

        self.modebutton.set_selected(task.value)

    @on(Events.Session, [State.started])
    def disable(self, sender=None, **kwargs):
        self.modebutton.set_sensitive(False)

    @on(Events.Session, [State.finished, State.stopped])
    def enable(self, sender=None, **kwargs):
        self.modebutton.set_sensitive(True)

    @property
    def widget(self):
        return self.modebutton
