import locale
import logging
from collections import namedtuple
from locale import gettext as _
from typing import Optional

from wiring import inject, SingletonScope
from wiring.scanning import register

from tomate.pomodoro import Sessions, State
from tomate.pomodoro.event import Subscriber, on, Events
from tomate.pomodoro.session import Payload as SessionPayload, Session
from .mode_button import ModeButton
from ..shortcut import ShortcutManager

locale.textdomain("tomate")
logger = logging.getLogger(__name__)

Shortcut = namedtuple("Shortcut", "name default session_type")


@register.factory("tomate.ui.taskbutton", scope=SingletonScope)
class TaskButton(Subscriber):
    @inject(session="tomate.session", shortcuts="tomate.ui.shortcut")
    def __init__(self, session: Session, shortcuts: ShortcutManager):
        self._session = session
        self._shortcuts = shortcuts

        self.widget = ModeButton(
            can_focus=False,
            homogeneous=True,
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
        )

        self._create_button(
            _("Pomodoro"),
            Shortcut(
                name="button.pomodoro",
                session_type=Sessions.pomodoro.value,
                default="<control>1",
            ),
        )

        self._create_button(
            _("Short Break"),
            Shortcut(
                name="button.shortbreak",
                session_type=Sessions.shortbreak.value,
                default="<control>2",
            ),
        )

        self._create_button(
            _("Long Break"),
            Shortcut(
                name="button.longbreak",
                session_type=Sessions.longbreak.value,
                default="<control>3",
            ),
        )

        self.widget.connect("mode_changed", self._on_mode_changed)

    def _create_button(self, label: str, shortcut: Shortcut):
        tooltip_text = "{} ({})".format(
            label, self._shortcuts.label(shortcut.name, shortcut.default)
        )
        self.widget.append_text(label, tooltip_text=tooltip_text)

        self._shortcuts.connect(
            shortcut.name,
            lambda *_: self.widget.set_selected(shortcut.session_type),
            shortcut.default,
        )

    def _on_mode_changed(self, _, index):
        session_type = Sessions.by_index(index)
        self._session.change(session=session_type)

    @on(Events.Session, [State.started])
    def disable(self, *args, **kwargs):
        self.widget.set_sensitive(False)

    @on(Events.Session, [State.finished, State.stopped])
    def enable(self, *args, payload: Optional[SessionPayload] = None):
        self.widget.set_sensitive(True)

        session_type = payload.type if payload else Sessions.pomodoro
        self.widget.set_selected(session_type.value)
