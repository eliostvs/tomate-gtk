from __future__ import unicode_literals

import unittest

import six
from mock import Mock, patch
from wiring import FactoryProvider, SingletonScope, Graph

from tomate.constant import State
from tomate.view import UI, TrayIcon


@patch('tomate_gtk.view.GdkPixbuf')
@patch('tomate_gtk.view.Gtk')
class TestGtkView(unittest.TestCase):

    def make_view(self):
        from tomate_gtk.view import GtkUI

        view = GtkUI(session=Mock(),
                     events=Mock(),
                     config=Mock(),
                     graph=Mock(),
                     toolbar=Mock(),
                     timerframe=Mock(),
                     taskbutton=Mock())

        return view

    def test_module(self, Gtk, GdkPixbuf):
        from tomate_gtk.view import ViewModule

        six.assertCountEqual(self, ['tomate.view'], ViewModule.providers.keys())

        graph = Graph()
        ViewModule().add_to(graph)
        provider = graph.providers['tomate.view']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)

        dependencies = dict(session='tomate.session',
                            events='tomate.events',
                            config='tomate.config',
                            graph=Graph,
                            toolbar='view.toolbar',
                            timerframe='view.timerframe',
                            taskbutton='view.taskbutton')

        self.assertDictEqual(dependencies, provider.dependencies)

    def test_should_call_gtk_main(self, Gtk, GdkPixbuf):
        view = self.make_view()

        view.run()

        Gtk.main.assert_called_once_with()

    def test_should_quit_when_timer_is_not_running(self, Gtk, GdkPixbuf):
        view = self.make_view()

        view.session.timer_is_running.return_value = False
        view.quit()

        Gtk.main_quit.assert_called_once_with()

    def test_should_minimize_when_timer_is_running_and_trayicon_is_not_in_providers(self, Gtk, GdkPixbuf):
        view = self.make_view()
        view.session.timer_is_running.return_value = True
        view.graph.providers = {}

        view.quit()

        view.event.send.assert_called_with(State.hiding)
        view.window.iconify.assert_called_once_with()

    def test_should_hide_when_timer_is_running_and_trayicon_is_in_providers(self, Gtk, GdkPixbuf):
        view = self.make_view()
        view.session.timer_is_running.return_value = True
        view.graph.providers = {TrayIcon: ''}

        view.quit()

        view.event.send.assert_called_with(State.hiding)
        view.window.hide_on_delete.assert_called_once_with()

    def test_interface(self, Gtk, GdkPixbuf):
        view = self.make_view()

        UI.check_compliance(view)
