import pytest
from gi.repository import Gtk, Gdk
from wiring import Graph
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.pomodoro import State
from tomate.pomodoro.event import Events, connect_events
from tomate.ui.widgets import Window, TaskButton, TrayIcon, Countdown, HeaderBar


@pytest.fixture()
def mock_taskbutton(mocker):
    return mocker.Mock(TaskButton, widget=Gtk.Label())


@pytest.fixture
def subject(
    graph, mock_shortcut, mock_taskbutton, dispatcher, mock_config, mock_session, mocker
):
    Events.Session.receivers.clear()

    graph.register_instance("tomate.session", mock_session)
    graph.register_instance(
        "tomate.ui.headerbar", mocker.Mock(HeaderBar, widget=Gtk.Label())
    )
    graph.register_instance(
        "tomate.ui.countdown", mocker.Mock(Countdown, widget=Gtk.Label())
    )
    graph.register_instance("tomate.ui.taskbutton", mock_taskbutton)
    graph.register_instance("tomate.ui.shortcut", mock_shortcut)
    graph.register_instance("tomate.events.view", dispatcher)
    graph.register_instance("tomate.config", mock_config)
    graph.register_instance(Graph, graph)
    scan_to_graph(["tomate.ui.widgets.window"], graph)
    instance = graph.get("tomate.ui.view")

    connect_events(instance)

    return instance


def test_module(graph, subject):
    instance = graph.get("tomate.ui.view")

    assert isinstance(instance, Window)
    assert instance is subject


def test_initializes_shortcuts(subject, mock_shortcut):
    assert mock_shortcut.initialize(subject.widget)


def test_enables_session_buttons(subject, mock_taskbutton):
    assert mock_taskbutton.enable.called_once_with()


def test_starts_loop(mocker, subject):
    gtk_main = mocker.patch("tomate.ui.widgets.window.Gtk.main")

    subject.run()

    gtk_main.assert_called_once_with()


def test_uses_correct_icon_size(subject, mock_config):
    mock_config.icon_path.assert_called_once_with("tomate", 22)


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

    def test_deletes_when_tray_icon_plugin_is_registered(
        self, subject, dispatcher, graph, mocker
    ):
        graph.register_factory(TrayIcon, mocker.Mock)

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.hid, weak=False)

        subject.widget.set_visible(True)

        result = subject.hide()

        assert result
        assert subject.widget.get_visible() is False
        subscriber.assert_called_once_with(State.hid)


class TestWindowQuit:
    def test_quits_when_timer_is_not_running(self, subject, mock_session, mocker):
        main_quit = mocker.patch("tomate.ui.widgets.window.Gtk.main_quit")
        mock_session.is_running.return_value = False

        subject.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        refresh_gui()

        main_quit.assert_called_once_with()

    def test_hides_when_timer_is_running(
        self, subject, mock_session, dispatcher, mocker
    ):
        mock_session.is_running.return_value = True

        subscriber = mocker.Mock()
        dispatcher.connect(subscriber, sender=State.hid, weak=False)

        subject.widget.emit("delete-event", Gdk.Event.new(Gdk.EventType.DELETE))

        subscriber.assert_called_once_with(State.hid)


def test_shows_window_when_session_finishes(subject, dispatcher, mocker):
    subject.widget.set_visible(False)

    subscriber = mocker.Mock()
    dispatcher.connect(subscriber, sender=State.showed, weak=False)

    Events.Session.send(State.finished)

    assert subject.widget.get_visible()
    subscriber.assert_called_once_with(State.showed)
