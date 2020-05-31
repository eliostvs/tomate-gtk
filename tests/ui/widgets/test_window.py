import random

import pytest
from gi.repository import Gtk
from wiring import Graph, SingletonScope
from wiring.scanning import scan_to_graph

from tomate.pomodoro import State
from tomate.pomodoro.event import Events
from tomate.ui.widgets import Countdown, HeaderBar, TaskButton, TrayIcon


@pytest.fixture
def task_button(mocker):
    return mocker.Mock(TaskButton, widget=Gtk.Label())


@pytest.fixture
def dispatcher(mocker):
    return mocker.Mock()


@pytest.fixture
def subject(
    graph, mocker, mock_shortcuts, task_button, dispatcher, mock_config, mock_session
):
    mocker.patch("tomate.ui.widgets.window.Gtk.Window")
    mocker.patch("tomate.ui.widgets.window.GdkPixbuf")

    from tomate.ui.widgets.window import Window

    Events.Session.receivers.clear()

    widget = Gtk.Label()

    return Window(
        session=mock_session,
        dispatcher=dispatcher,
        config=mock_config,
        graph=graph,
        headerbar=mocker.Mock(HeaderBar, widget=widget),
        countdown=mocker.Mock(Countdown, widget=widget),
        task_button=task_button,
        shortcuts=mock_shortcuts,
    )


def test_module(graph):
    spec = "tomate.ui.view"
    package = "tomate.ui.widgets.window"

    scan_to_graph([package], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    dependencies = dict(
        session="tomate.session",
        dispatcher="tomate.events.view",
        config="tomate.config",
        graph=Graph,
        headerbar="tomate.ui.headerbar",
        countdown="tomate.ui.countdown",
        task_button="tomate.ui.taskbutton",
        shortcuts="tomate.ui.shortcuts",
    )

    assert sorted(provider.dependencies) == sorted(dependencies)


def test_initialize_shortcuts_and_session_buttons(subject, task_button, mock_shortcuts):
    # when
    assert task_button.enable.called_once_with()
    assert mock_shortcuts.initialize(subject.widget)


def test_call_gtk_main_on_run(mocker, subject):
    # given
    gtk_main = mocker.patch("tomate.ui.widgets.window.Gtk.main")

    # when
    subject.run()

    # then
    gtk_main.assert_called_once_with()


def describe_hide():
    def test_minimize_when_none_tray_plugin_is_enabled(subject, dispatcher, graph):
        # given
        graph.providers.clear()

        # when
        assert subject.hide() is Gtk.true

        # then
        dispatcher.send.assert_called_with(State.hid)
        subject.widget.iconify.assert_called_once_with()

    def test_hide_in_tray_when_a_tray_plugin_is_enabled(
        subject, dispatcher, graph, mocker
    ):
        # given
        graph.register_factory(TrayIcon, mocker.Mock)

        return_value = random.random()
        subject.widget.hide_on_delete.return_value = return_value

        # when
        assert subject.hide() is return_value

        # then
        dispatcher.send.assert_called_with(State.hid)


def describe_quit():
    def test_quit_when_timer_is_not_running(mocker, subject, mock_session):
        # given
        main_quit = mocker.patch("tomate.ui.widgets.window.Gtk.main_quit")
        mock_session.IsRunning.return_value = False

        # when
        subject.quit()

        # then
        main_quit.assert_called_once_with()

    def test_hide_when_timer_is_running(subject, mocker, mock_session):
        # given
        subject.hide = mocker.Mock()
        mock_session.IsRunning.return_value = True

        # when
        subject.quit()

        # then
        subject.hide.assert_called_once_with()


def describe_session_lifecycle():
    def test_show_window_when_session_finishes(subject, mocker, dispatcher):
        # when
        Events.Session.send(State.finished)

        # then
        dispatcher.send.assert_called_once_with(State.showed)
        subject.widget.present_with_time_once(mocker.ANY)
