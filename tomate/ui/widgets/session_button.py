import locale
import logging
from locale import gettext as _
from typing import Callable, Union

import blinker
from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import Events, Session, SessionEndPayload, SessionPayload, SessionType, Subscriber, on
from tomate.ui import Shortcut, ShortcutEngine
from .mode_button import ModeButton

locale.textdomain("tomate")
logger = logging.getLogger(__name__)


@register.factory("tomate.ui.taskbutton", scope=SingletonScope)
class SessionButton(Subscriber):
    POMODORO_SHORTCUT = Shortcut("session.pomodoro", "<control>1")
    SHORT_BREAK_SHORTCUT = Shortcut("session.short_break", "<control>2")
    LONG_BREAK_SHORTCUT = Shortcut("session.long_break", "<control>3")

    @inject(
        bus="tomate.bus",
        session="tomate.session",
        shortcuts="tomate.ui.shortcut",
    )
    def __init__(self, bus: blinker.Signal, session: Session, shortcuts: ShortcutEngine):
        self.connect(bus)
        self._session = session

        self.widget = ModeButton(
            can_focus=False,
            homogeneous=True,
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
        )

        self.widget.append_text(
            _("Pomodoro"),
            tooltip_text=_("Pomodoro ({})".format(shortcuts.label(SessionButton.POMODORO_SHORTCUT))),
            name=SessionButton.POMODORO_SHORTCUT.name,
        )
        shortcuts.connect(SessionButton.POMODORO_SHORTCUT, self._change_session(SessionType.POMODORO))

        self.widget.append_text(
            _("Short Break"),
            tooltip_text=_("Short Break ({})".format(shortcuts.label(SessionButton.SHORT_BREAK_SHORTCUT))),
            name=SessionButton.SHORT_BREAK_SHORTCUT.name,
        )
        shortcuts.connect(SessionButton.SHORT_BREAK_SHORTCUT, self._change_session(SessionType.SHORT_BREAK))

        self.widget.append_text(
            _("Long Break"),
            tooltip_text=_("Long Break ({})".format(shortcuts.label(SessionButton.LONG_BREAK_SHORTCUT))),
            name=SessionButton.LONG_BREAK_SHORTCUT.name,
        )
        shortcuts.connect(SessionButton.LONG_BREAK_SHORTCUT, self._change_session(SessionType.LONG_BREAK))

        self.widget.connect("mode_changed", self._on_button_clicked)

    def _change_session(self, session_type: SessionType) -> Callable[[], bool]:
        def callback(*_) -> bool:
            logger.debug("action=change session=%s", session_type)
            self.widget.set_selected(session_type.value)
            return True

        return callback

    def _on_button_clicked(self, _, number):
        session_type = SessionType.of(number)
        logger.debug("action=mode_changed session=%s", session_type)
        self._session.change(session=session_type)

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
