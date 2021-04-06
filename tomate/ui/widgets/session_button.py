import locale
import logging
from collections import namedtuple
from locale import gettext as _
from typing import Union

import blinker
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro.event import Events, Subscriber, on
from tomate.pomodoro.session import (
    EndPayload as SessionEndPayload,
    Payload as SessionPayload,
    Session,
    Type as SessionType,
)
from .mode_button import ModeButton
from ..shortcut import ShortcutManager

locale.textdomain("tomate")
logger = logging.getLogger(__name__)

Shortcut = namedtuple("Shortcut", "name default session_type")


@register.factory("tomate.ui.taskbutton", scope=SingletonScope)
class SessionButton(Subscriber):
    @inject(
        bus="tomate.bus",
        session="tomate.session",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(self, bus: blinker.Signal, session: Session, shortcuts: ShortcutManager):
        self.connect(bus)
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
                session_type=SessionType.POMODORO.value,
                default="<control>1",
            ),
        )

        self._create_button(
            _("Short Break"),
            Shortcut(
                name="button.shortbreak",
                session_type=SessionType.SHORT_BREAK.value,
                default="<control>2",
            ),
        )

        self._create_button(
            _("Long Break"),
            Shortcut(
                name="button.longbreak",
                session_type=SessionType.LONG_BREAK.value,
                default="<control>3",
            ),
        )

        self.widget.connect("mode_changed", self._on_mode_changed)

    def _create_button(self, label: str, shortcut: Shortcut):
        tooltip_text = "{} ({})".format(label, self._shortcuts.label(shortcut.name, shortcut.default))
        self.widget.append_text(label, tooltip_text=tooltip_text)

        self._shortcuts.connect(
            shortcut.name,
            lambda *_: self.widget.set_selected(shortcut.session_type),
            shortcut.default,
        )

    def _on_mode_changed(self, _, number):
        logger.debug("action=change session=%s", SessionType.of(number))
        self._session.change(session=SessionType.of(number))

    def init(self):
        self.widget.set_sensitive(True)
        self.widget.set_selected(SessionType.POMODORO.value)

    @on(Events.SESSION_START)
    def _on_session_start(self, *_, **__):
        logger.debug("action=disable")
        self.widget.set_sensitive(False)

    @on(Events.SESSION_INTERRUPT, Events.SESSION_END)
    def _on_session_stop(self, _, payload: Union[SessionPayload, SessionEndPayload]):
        logger.debug("action=enable session=%s", payload.type)
        self.widget.set_sensitive(True)
        self.widget.set_selected(payload.type.value)
