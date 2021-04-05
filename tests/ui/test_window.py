import pytest
from gi.repository import Gdk, Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import assert_shortcut_called, create_session_end_payload, create_session_payload
from tomate.pomodoro.event import Bus, Events, connect_events
from tomate.ui import Window
from tomate.ui.widgets import TrayIcon


@pytest.fixture
def subject(graph, bus, config, session):
    Bus.receivers.clear()
    graph.register_instance("tomate.session", session)
    graph.register_instance("tomate.bus", bus)
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


def test_shortcuts(subject, graph):
    shortcut_manager = graph.get("tomate.ui.shortcut")

    assert_shortcut_called(shortcut_manager, "<control>s", window=subject.widget)


def test_start(mocker, subject):
    gtk_main = mocker.patch("tomate.ui.window.Gtk.main")
    show_all = mocker.patch("tomate.ui.window.Gtk.Window.show_all")

    subject.run()

    gtk_main.assert_called_once_with()
    show_all.assert_called_once_with()


class TestWindowHide:
    def test_iconify_when_tray_icon_plugin_is_not_registered(self, subject, bus, graph, mocker):
        graph.providers.clear()
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.WINDOW_HIDE, weak=False)

        result = subject.hide()

        assert result is Gtk.true
        subscriber.assert_called_once_with(Events.WINDOW_HIDE)

    def test_deletes_when_tray_icon_plugin_is_registered(self, subject, bus, graph, mocker):
        graph.register_factory(TrayIcon, mocker.Mock)
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.WINDOW_HIDE, weak=False)
        subject.widget.set_visible(True)

        result = subject.hide()

        assert result
        assert subject.widget.get_visible() is False
        subscriber.assert_called_once_with(Events.WINDOW_HIDE)


class TestWindowQuit:
    def test_quits_when_timer_is_not_running(self, subject, session, mocker):
        main_quit = mocker.patch("tomate.ui.window.Gtk.main_quit")
        session.is_running.return_value = False

        subject.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        main_quit.assert_called_once_with()

    def test_hides_when_timer_is_running(self, subject, session, bus, mocker):
        session.is_running.return_value = True
        subscriber = mocker.Mock()
        bus.connect(subscriber, sender=Events.WINDOW_HIDE, weak=False)

        subject.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        subscriber.assert_called_once_with(Events.WINDOW_HIDE)


def test_shows_window_when_session_end(subject, bus, mocker):
    subject.widget.set_visible(False)
    subscriber = mocker.Mock()
    bus.connect(subscriber, sender=Events.WINDOW_SHOW, weak=False)
    payload = create_session_end_payload(previous=create_session_payload())

    Bus.send(Events.SESSION_END, payload=payload)

    assert subject.widget.get_visible()
    subscriber.assert_called_once_with(Events.WINDOW_SHOW)
