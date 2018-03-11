import locale
import logging
from gi.repository import Gtk
from locale import gettext as _

from tomate.constant import State
from tomate.event import Subscriber, on, Events
from wiring import inject, SingletonScope
from wiring.scanning import register

locale.textdomain('tomate')
logger = logging.getLogger(__name__)


@register.factory('view.taskentry', scope=SingletonScope)
class TaskEntry(Subscriber):
    @inject(session='tomate.session')
    def __init__(self, session):
        self.session = session

        self.widget = Gtk.Entry(
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
            margin_top=12,
            max_length=20,
            placeholder_text=_('Enter task name...'),
            secondary_icon_name='gtk-clear',
            xalign=0.5,
            sensitive=True
        )

        self.widget.set_icon_sensitive(1, False)

        self.widget.connect('changed', self.on_changed_text)
        self.widget.connect('icon-press', self.on_icon_press)

    def on_icon_press(self, widget, icon_pos, event):
        widget.set_text('')
        widget.get_toplevel().set_focus(None)

    def on_changed_text(self, widget):
        task_name = widget.get_text().strip()

        if task_name:
            self.session.task_name = task_name
            widget.set_icon_sensitive(1, True)
        else:
            widget.set_icon_sensitive(1, False)

    @on(Events.Session, [State.started])
    def disable(self, sender=None, **kwargs):
        self.widget.set_sensitive(False)

    @on(Events.Session, [State.finished, State.stopped])
    def enable(self, sender=None, **kwargs):
        self.widget.set_sensitive(True)
