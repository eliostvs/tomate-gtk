from os.path import dirname, join
from unittest.mock import patch

import gi
import pytest

from tomate.pomodoro import Config, Events, SessionType
from tomate.ui.testing import create_session_payload

gi.require_version("Notify", "0.7")

IconPath = join(dirname(dirname(__file__)), "data", "icons", "hicolor", "24x24", "apps", "tomate.png")


@pytest.fixture
@patch("gi.repository.Notify.Notification.new")
def plugin(_, graph, bus):
    graph.providers.clear()
    graph.register_instance("tomate.bus", bus)
    graph.register_instance("tomate.config", Config(bus))

    from notify import NotifyPlugin

    instance = NotifyPlugin()
    instance.configure(bus, graph)
    return instance


@patch("gi.repository.Notify.init")
def test_enable_notify_when_plugin_active(init, plugin):
    plugin.activate()

    init.assert_called_with("tomate-notify-plugin")


@patch("gi.repository.Notify.uninit")
def test_disable_notify_when_plugin_deactivate(uninit, plugin):
    plugin.deactivate()

    uninit.assert_called_with()


@pytest.mark.parametrize(
    "event,session,title,message",
    [
        (Events.SESSION_START, SessionType.POMODORO, "Pomodoro", "Get back to work!"),
        (Events.SESSION_START, SessionType.SHORT_BREAK, "Short Break", "It's coffee time!"),
        (Events.SESSION_START, SessionType.LONG_BREAK, "Long Break", "Step away from the machine!"),
        (Events.SESSION_INTERRUPT, SessionType.POMODORO, "Session stopped manually", ""),
        (Events.SESSION_END, SessionType.POMODORO, "The time is up!", ""),
    ],
)
def test_show_notification_when_session_starts(event, session, title, message, bus, plugin):
    plugin.activate()

    payload = create_session_payload(type=session)
    bus.send(event, payload=payload)

    plugin.notification.update.assert_called_once_with(title, message, IconPath)
    plugin.notification.show.assert_called_once()
