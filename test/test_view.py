from __future__ import unicode_literals

import pytest
from mock import Mock, patch
from tomate.constant import State
from tomate.view import UI, TrayIcon
from wiring import Graph


@pytest.fixture()
@patch('tomate_gtk.view.Gtk')
@patch('tomate_gtk.view.GdkPixbuf')
def gtkui(Gtk, GdkPixBuf):
    from tomate_gtk.view import GtkUI

    return GtkUI(session=Mock(),
                 events=Mock(),
                 config=Mock(),
                 graph=Mock(),
                 toolbar=Mock(),
                 timerframe=Mock(),
                 taskbutton=Mock())


def test_module(graph):
    assert 'tomate.view' in graph.providers

    provider = graph.providers['tomate.view']

    dependencies = dict(session='tomate.session',
                        events='tomate.events',
                        config='tomate.config',
                        graph=Graph,
                        toolbar='view.toolbar',
                        timerframe='view.timerframe',
                        taskbutton='view.taskbutton')

    assert provider.dependencies == dependencies


@patch('tomate_gtk.view.Gtk')
def test_should_call_gtk_main(Gtk, gtkui):
    gtkui.run()

    Gtk.main.assert_called_once_with()


@patch('tomate_gtk.view.Gtk')
def test_should_quit_when_timer_is_not_running(Gtk, gtkui):
    gtkui.session.is_running.return_value = False
    gtkui.quit()

    Gtk.main_quit.assert_called_once_with()


def test_should_minimize_when_timer_is_running_and_trayicon_is_not_in_providers(gtkui):
    gtkui.session.timer_is_running.return_value = True
    gtkui.graph.providers = {}

    gtkui.quit()

    gtkui.event.send.assert_called_with(State.hid)
    gtkui.window.iconify.assert_called_once_with()


def test_should_hide_when_timer_is_running_and_trayicon_is_in_providers(gtkui):
    gtkui.session.timer_is_running.return_value = True
    gtkui.graph.providers = {TrayIcon: ''}

    gtkui.quit()

    gtkui.event.send.assert_called_with(State.hid)
    gtkui.window.hide_on_delete.assert_called_once_with()


def test_interface_compliance(gtkui):
    UI.check_compliance(gtkui)
