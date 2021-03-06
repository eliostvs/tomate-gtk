import locale
import logging
from locale import gettext as _
from typing import Optional

from tomate.constant import Sessions, State
from tomate.event import Subscriber, on, Events
from tomate.session import SessionPayload
from wiring import inject, SingletonScope
from wiring.scanning import register

from .mode_button import ModeButton

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("view.taskbutton", scope=SingletonScope)
class TaskButton(Subscriber):
    @inject(session="tomate.session")
    def __init__(self, session):
        self.session = session

        self.widget = ModeButton(
            can_focus=False,
            homogeneous=True,
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
        )

        self.widget.append_text(_("Pomodoro"))
        self.widget.append_text(_("Short Break"))
        self.widget.append_text(_("Long Break"))

        self.widget.connect("mode_changed", self.on_mode_changed)

    def on_mode_changed(self, _, index):
        session_type = Sessions.by_index(index)

        self.session.change(session=session_type)

    @on(Events.Session, [State.started])
    def disable(self, *args, **kwargs):
        self.widget.set_sensitive(False)

    @on(Events.Session, [State.finished, State.stopped])
    def enable(self, sender=None, payload: Optional[SessionPayload] = None):
        self.widget.set_sensitive(True)

        session_type = payload.type if payload else Sessions.pomodoro

        self.widget.set_selected(session_type.value)
