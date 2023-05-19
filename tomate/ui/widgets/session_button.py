import locale
import logging
from locale import gettext as _
from typing import Callable

from wiring import SingletonScope, inject
from wiring.scanning import register

from tomate.pomodoro import (Bus, Events, Session, SessionPayload, SessionType,
                             Subscriber, on)
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
    def __init__(self, bus: Bus, session: Session, shortcuts: ShortcutEngine):
        self.connect(bus)
        self._session = session
        self._shortcuts = shortcuts

        self.widget = self._create_mode_button()
        self._add_button(SessionButton.POMODORO_SHORTCUT, "Pomodoro", SessionType.POMODORO)
        self._add_button(SessionButton.SHORT_BREAK_SHORTCUT, "Short Break", SessionType.SHORT_BREAK)
        self._add_button(SessionButton.LONG_BREAK_SHORTCUT, "Long Break", SessionType.LONG_BREAK)
        self.widget.connect("mode_changed", self._clicked)

    def _create_mode_button(self) -> ModeButton:
        return ModeButton(
            can_focus=False,
            homogeneous=True,
            margin_bottom=12,
            margin_left=12,
            margin_right=12,
            sensitive=True,
        )

    def _add_button(self, shortcut: Shortcut, label: str, session_type: SessionType) -> None:
        self.widget.append_text(
            _(label),
            tooltip_text=_("{} ({})".format(label, self._shortcuts.label(shortcut))),
            name=shortcut.name,
        )
        self._shortcuts.connect(shortcut, self._select(session_type))

    def _select(self, session_type: SessionType) -> Callable[[], bool]:
        def callback(*_) -> bool:
            logger.debug("action=change session=%s", session_type)
            self.widget.set_selected(session_type.value)
            return True

        return callback

    def _clicked(self, _, number):
        session_type = SessionType.of(number)
        logger.debug("action=mode_changed session=%s", session_type)
        self._session.change(session_type)

    @on(Events.SESSION_CHANGE)
    def _change(self, payload=SessionPayload) -> None:
        logger.debug("action=change current=%d next=%d", self.widget.get_selected(), payload.type.value)
        if self.widget.get_selected() != payload.type.value:
            self._enable(payload)

    @on(Events.SESSION_START)
    def _disable(self, **__):
        logger.debug("action=disable")
        self.widget.props.sensitive = False

    @on(Events.SESSION_READY, Events.SESSION_INTERRUPT)
    def _enable(self, payload: SessionPayload):
        logger.debug("action=enable session=%s", payload.type)
        self.widget.props.sensitive = True
        self.widget.set_selected(payload.type.value)
