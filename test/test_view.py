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
def ui(mocker, shortcut_manager, task_button):
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


def test_interface_compliance(ui):
    UI.check_compliance(ui)


def test_module(graph):
    scan_to_graph(["tomate_gtk.view"], graph)

    assert "tomate.view" in graph.providers

    provider = graph.providers["tomate.view"]

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
            self, ui, task_button, shortcut_manager
    ):
        # when
        assert task_button.enable.called_once_with()
        assert shortcut_manager.initialize(ui.widget)


class TestRun:
    def test_should_call_gtk_main(self, mocker, ui):
        # given
        gtk = mocker.patch("tomate_gtk.view.Gtk")

        # when
        ui.run()

        # then
        gtk.main.assert_called_once_with()


class TestHide:
    def test_should_minimize_when_none_tray_plugin_is_enabled(self, ui):
        # given
        ui.graph.providers = {}

        # when
        assert ui.hide() is Gtk.true

        # then
        ui.dispatcher.send.assert_called_with(State.hid)
        ui.widget.iconify.assert_called_once_with()

    def test_should_hide_in_tray_when_a_tray_plugin_is_enabled(self, ui):
        # given
        ui.graph.providers = {TrayIcon: ""}

        return_value = random.random()
        ui.widget.hide_on_delete.return_value = return_value

        # when
        assert ui.hide() is return_value

        # then
        ui.dispatcher.send.assert_called_with(State.hid)


class TestQuit:
    def test_should_quit_when_timer_is_not_running(self, mocker, ui):
        # given
        gtk = mocker.patch("tomate_gtk.view.Gtk")
        ui.session.is_running.return_value = False

        # when
        ui.quit()

        # then
        gtk.main_quit.assert_called_once_with()

    def test_should_hide_when_timer_is_running(self, ui, mocker):
        # given
        ui.hide = mocker.Mock()
        ui.session.is_running.return_value = True

        # when
        ui.quit()

        # then
        ui.hide.assert_called_once_with()


class TestShow:
    def test_should_present_window(self, ui, mocker):
        # when
        Events.Session.send(State.finished)

        # then
        ui.dispatcher.send.assert_called_once_with(State.showed)
        ui.widget.present_with_time_once(mocker.ANY)
