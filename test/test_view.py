import pytest
from gi.repository import Gtk
from wiring import Graph, SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State
from tomate.view import UI, TrayIcon


@pytest.fixture
def gtkui(mocker):
    mocker.patch('tomate_gtk.view.Gtk')
    mocker.patch('tomate_gtk.view.GdkPixbuf')

    from tomate_gtk.view import GtkUI

    return GtkUI(session=mocker.Mock(),
                 event=mocker.Mock(),
                 config=mocker.Mock(),
                 graph=mocker.Mock(),
                 headerbar=mocker.Mock(),
                 timer_frame=mocker.Mock(),
                 task_button=mocker.Mock(),
                 infobar=mocker.Mock(),
                 task_entry=mocker.Mock())


def test_view_module(graph):
    scan_to_graph(['tomate_gtk.view'], graph)

    assert 'tomate.view' in graph.providers

    provider = graph.providers['tomate.view']

    assert provider.scope == SingletonScope

    dependencies = dict(session='tomate.session',
                        event='tomate.events.view',
                        config='tomate.config',
                        graph=Graph,
                        headerbar='view.headerbar',
                        timer_frame='view.timerframe',
                        task_button='view.taskbutton',
                        infobar='view.infobar',
                        task_entry='view.taskentry')

    assert sorted(provider.dependencies) == sorted(dependencies)


def test_should_call_gtk_main(mocker, gtkui):
    gtk = mocker.patch('tomate_gtk.view.Gtk')

    gtkui.run()

    gtk.main.assert_called_once_with()


def test_should_quit_when_timer_is_not_running(mocker, gtkui):
    gtk = mocker.patch('tomate_gtk.view.Gtk')

    gtkui.session.is_running.return_value = False
    gtkui.quit()

    gtk.main_quit.assert_called_once_with()


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


def test_show_message(gtkui):
    gtkui.show_message('message', Gtk.MessageType.INFO)

    gtkui.infobar.show_message.assert_called_with('message', Gtk.MessageType.INFO)


def test_should_should_window(gtkui, mocker):
    gtkui.show()

    gtkui.event.send.assert_called_once_with(State.showed)
    gtkui.window.present_with_time_once(mocker.ANY)
