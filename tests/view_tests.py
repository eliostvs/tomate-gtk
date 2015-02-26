from __future__ import unicode_literals

import unittest

from mock import Mock, patch


class GtkViewTestCase(unittest.TestCase):

    def test_interface(self):
        from tomate_gtk.view import GtkView
        from tomate.view import IView

        view = GtkView()

        IView.check_compliance(view)


class TestGtkViewTestCase(unittest.TestCase):

    def setUp(self):
        from tomate_gtk.view import GtkView

        self.view = GtkView(session=Mock(), window=Mock(), signals=Mock())

    def test_quit_when_session_is_running(self):
        self.view.session.timer_is_running.return_value = True
        self.view.quit()

        self.view.window.hide_on_delete.assert_called_once_with()

    @patch('tomate_gtk.view.Gtk')
    def test_quit_when_session_is_not_running(self, gtk):
        self.view.session.timer_is_running.return_value = False
        self.view.quit()

        gtk.main_quit.assert_called_once_with()
