import pytest
from gi.repository import Gtk, Gdk
from wiring.scanning import scan_to_graph

from tests.conftest import assert_shortcut_called
from tomate.pomodoro import State, Sessions
from tomate.pomodoro.event import Events, connect_events
from tomate.pomodoro.session import Payload as SessionPayload
from tomate.ui import Window
from tomate.ui.widgets import TrayIcon


@pytest.fixture
def subject(graph, dispatcher, config, session):
    Events.Session.receivers.clear()

    graph.register_instance("tomate.session", session)
    graph.register_instance("tomate.events.view", dispatcher)
    graph.register_instance("tomate.config", config)

    namespaces = [
        "tomate.ui",
        "tomate.pomodoro.plugin",
        "tomate.pomodoro.proxy",
    ]
    scan_to_graph(namespaces, graph)
    instance = graph.get("tomate.ui.view")

    connect_events(instance)

    return instance


def test_module(graph, subject):
    instance = graph.get("tomate.ui.view")

    assert isinstance(instance, Window)
    assert instance is subject


def test_shortcuts_are_connected(subject, graph):
    shortcut_manager = graph.get("tomate.ui.shortcut")

    assert_shortcut_called(shortcut_manager, "<control>s", window=subject.widget)


def test_starts_loop(mocker, subject):
    gtk_main = mocker.patch("tomate.ui.window.Gtk.main")
    show_all = mocker.patch("tomate.ui.window.Gtk.Window.show_all")

    subject.run()

    gtk_main.assert_called_once_with()
    show_all.assert_called_once_with()


class TestWindowHide:
    def test_iconify_when_tray_icon_plugin_is_not_registered(
        self, subject, dispatcher, graph, mocker
    ):
        graph.providers.clear()

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.hid, weak=False)

        result = subject.hide()

        assert result is Gtk.true
        subscriber.assert_called_once_with(State.hid)

    def test_deletes_when_tray_icon_plugin_is_registered(self, subject, dispatcher, graph, mocker):
        graph.register_factory(TrayIcon, mocker.Mock)

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.hid, weak=False)

        subject.widget.set_visible(True)

        result = subject.hide()

        assert result
        assert subject.widget.get_visible() is False
        subscriber.assert_called_once_with(State.hid)


class TestWindowQuit:
    def test_quits_when_timer_is_not_running(self, subject, session, mocker):
        main_quit = mocker.patch("tomate.ui.window.Gtk.main_quit")
        session.is_running.return_value = False

        subject.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        main_quit.assert_called_once_with()

    def test_hides_when_timer_is_running(self, subject, session, dispatcher, mocker):
        session.is_running.return_value = True

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.hid, weak=False)

        subject.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        subscriber.assert_called_once_with(State.hid)


def test_shows_window_when_session_finishes(subject, dispatcher, mocker):
    subject.widget.set_visible(False)

    subscriber = mocker.Mock()
    dispatcher.connect(subscriber, sender=State.showed, weak=False)

    payload = SessionPayload(
        id="",
        type=Sessions.pomodoro,
        pomodoros=0,
        state=State.started,
        duration=0,
    )
    Events.Session.send(State.finished, payload=payload)

    assert subject.widget.get_visible()
    subscriber.assert_called_once_with(State.showed)
