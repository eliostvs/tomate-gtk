import random

import pytest
from gi.repository import Gtk
from wiring import Graph, SingletonScope
from wiring.scanning import scan_to_graph

from tomate.config import Config
from tomate.constant import State
from tomate.event import Events
from tomate.session import Session
from tomate.view import UI, TrayIcon
from tomate_gtk.shortcut import ShortcutManager
from tomate_gtk.widgets.countdown import Countdown
from tomate_gtk.widgets.headerbar import HeaderBar
from tomate_gtk.widgets.task_button import TaskButton


@pytest.fixture
def shortcut_manager(mocker):
    return mocker.Mock(ShortcutManager)


@pytest.fixture
def task_button(mocker):
    return mocker.Mock(TaskButton, widget=Gtk.Label())


@pytest.fixture
def subject(mocker, shortcut_manager, task_button):
    mocker.patch("tomate_gtk.view.Gtk.Window")
    mocker.patch("tomate_gtk.view.GdkPixbuf")

    from tomate_gtk.view import GtkUI

    Events.Session.receivers.clear()

    widget = Gtk.Label()

    return GtkUI(
        session=mocker.Mock(Session),
        dispatcher=mocker.Mock(Events.View),
        config=mocker.Mock(Config),
        graph=mocker.Mock(),
        headerbar=mocker.Mock(HeaderBar, widget=widget),
        countdown=mocker.Mock(Countdown, widget=widget),
        task_button=task_button,
        shortcuts=shortcut_manager,
    )


def test_interface_compliance(subject):
    UI.check_compliance(subject)


def test_module(graph):
    spec = "tomate.view"

    scan_to_graph(["tomate_gtk.view"], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    dependencies = dict(
        session="tomate.session",
        dispatcher="tomate.events.view",
        config="tomate.config",
        graph=Graph,
        headerbar="view.headerbar",
        countdown="view.countdown",
        task_button="view.taskbutton",
        shortcuts="view.shortcuts",
    )

    assert sorted(provider.dependencies) == sorted(dependencies)


class TestInitialize:
    def test_should_initialize_shortcuts_and_session_buttons(
        self, subject, task_button, shortcut_manager
    ):
        # when
        assert task_button.enable.called_once_with()
        assert shortcut_manager.initialize(subject.widget)


class TestRun:
    def test_should_call_gtk_main(self, mocker, subject):
        # given
        gtk = mocker.patch("tomate_gtk.view.Gtk")

        # when
        subject.run()

        # then
        gtk.main.assert_called_once_with()


class TestHide:
    def test_should_minimize_when_none_tray_plugin_is_enabled(self, subject):
        # given
        subject.graph.providers = {}

        # when
        assert subject.hide() is Gtk.true

        # then
        subject.dispatcher.send.assert_called_with(State.hid)
        subject.widget.iconify.assert_called_once_with()

    def test_should_hide_in_tray_when_a_tray_plugin_is_enabled(self, subject):
        # given
        subject.graph.providers = {TrayIcon: ""}

        return_value = random.random()
        subject.widget.hide_on_delete.return_value = return_value

        # when
        assert subject.hide() is return_value

        # then
        subject.dispatcher.send.assert_called_with(State.hid)


class TestQuit:
    def test_should_quit_when_timer_is_not_running(self, mocker, subject):
        # given
        gtk = mocker.patch("tomate_gtk.view.Gtk")
        subject.session.is_running.return_value = False

        # when
        subject.quit()

        # then
        gtk.main_quit.assert_called_once_with()

    def test_should_hide_when_timer_is_running(self, subject, mocker):
        # given
        subject.hide = mocker.Mock()
        subject.session.is_running.return_value = True

        # when
        subject.quit()

        # then
        subject.hide.assert_called_once_with()


class TestShow:
    def test_should_present_window(self, subject, mocker):
        # when
        Events.Session.send(State.finished)

        # then
        subject.dispatcher.send.assert_called_once_with(State.showed)
        subject.widget.present_with_time_once(mocker.ANY)
