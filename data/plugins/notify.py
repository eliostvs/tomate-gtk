import logging
from locale import gettext as _

import gi
from wiring import Graph

from tomate.pomodoro import (
    Bus,
    Event,
    Events,
    SessionPayload,
    SessionType,
    on,
    plugin,
    suppress_errors,
)

gi.require_version("Notify", "0.7")

from gi.repository import Notify

logger = logging.getLogger(__name__)


class NotifyPlugin(plugin.Plugin):
    messages = {
        SessionType.POMODORO: {"title": _("Pomodoro"), "content": _("Get back to work!")},
        SessionType.SHORT_BREAK: {"title": _("Short Break"), "content": _("It's coffee time!")},
        SessionType.LONG_BREAK: {"title": _("Long Break"), "content": _("Step away from the machine!")},
    }

    @suppress_errors
    def __init__(self):
        super().__init__()
        self.notification = Notify.Notification.new("tomate-notify-plugin")

    def configure(self, bus: Bus, graph: Graph) -> None:
        super().configure(bus, graph)
        self.config = graph.get("tomate.config")

    @suppress_errors
    def activate(self):
        super().activate()
        Notify.init("tomate-notify-plugin")

    @suppress_errors
    def deactivate(self):
        super().deactivate()
        Notify.uninit()

    @on(Events.SESSION_START)
    def on_session_started(self, event: Event[SessionPayload]):
        session = event.payload
        if session is None:
            return

        self.show_notification(*self.get_message(session.type))

    @on(Events.SESSION_END)
    def on_session_finished(self, _event: Event[SessionPayload]):
        self.show_notification(title="The time is up!")

    @on(Events.SESSION_INTERRUPT)
    def on_session_stopped(self, _event: Event[SessionPayload]):
        self.show_notification(title="Session stopped manually")

    def get_message(self, session: SessionType) -> tuple[str, str]:
        return (
            self.messages[session]["title"],
            self.messages[session]["content"],
        )

    @suppress_errors
    def show_notification(self, title, message=""):
        self.notification.update(title, message, self.icon_path)
        result = self.notification.show()

        logger.debug(
            'action=show title="%s" message="%s" success=%r icon=%s',
            title,
            message,
            result,
            self.icon_path,
        )

    @property
    def icon_path(self):
        return self.config.icon_path("tomate", 32)
