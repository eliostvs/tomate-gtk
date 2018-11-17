import pytest
from conftest import refresh_gui
from gi.repository import Gtk
from tomate.constant import State
from tomate.event import Session, connect_events
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.widgets import HeaderBar


@pytest.fixture
def tomate_session(mocker):
    return mocker.Mock()


@pytest.fixture
def header_bar(tomate_session, mocker):
    Session.receivers.clear()

    subject = HeaderBar(tomate_session, mocker.Mock(widget=Gtk.Menu()))
    connect_events(subject)

    return subject


def test_header_bar_module(graph, mocker):
    scan_to_graph(['tomate_gtk.widgets.headerbar'], graph)

    assert 'view.headerbar' in graph.providers

    graph.register_instance('view.menu', mocker.Mock(widget=Gtk.Menu()))
    graph.register_instance('tomate.session', mocker.Mock())

    provider = graph.providers['view.headerbar']
    assert provider.scope == SingletonScope

    assert isinstance(graph.get('view.headerbar'), HeaderBar)


class TestSessionStart:
    def test_buttons_visibility(self, header_bar):
        Session.send(State.started)

        assert header_bar.start_button.get_visible() is False
        assert header_bar.stop_button.get_visible() is True
        assert header_bar.reset_button.get_sensitive() is False

    def test_start_session_on_button_clicked(self, header_bar, tomate_session):
        header_bar.start_button.emit('clicked')

        refresh_gui(0)

        tomate_session.start.assert_called_once_with()


class TestSessionStop:
    def test_buttons_visibility_with_no_sessions(self, header_bar):
        Session.send(State.stopped, sessions=0)

        assert header_bar.start_button.get_visible() is True
        assert header_bar.stop_button.get_visible() is False
        assert header_bar.reset_button.get_sensitive() is False

    def test_buttons_visibility_with_one_session(self, header_bar):
        Session.send(State.stopped, sessions=1)

        assert header_bar.start_button.get_visible() is True
        assert header_bar.stop_button.get_visible() is False
        assert header_bar.reset_button.get_sensitive() is True

    def test_header_title_with_no_sessions(self, header_bar):
        Session.send(State.stopped, sessions=0)

        assert header_bar.widget.props.title == 'No session yet'

    def test_header_title_with_one_session(self, header_bar):
        Session.send(State.stopped, sessions=1)

        assert header_bar.widget.props.title == 'Session 1'

    def test_stop_session_when_stop_button_is_clicked(self, header_bar, tomate_session):
        header_bar.stop_button.emit('clicked')

        refresh_gui(0)

        tomate_session.stop.assert_called_once_with()


class TestSessionReset:
    def test_buttons_visibility(self, header_bar):
        header_bar.reset_button.set_sensitive(True)

        Session.send(State.reset)

        assert header_bar.reset_button.get_sensitive() is False

    def test_reset_session_when_reset_button_is_clicked(self, header_bar, tomate_session):
        header_bar.reset_button.emit('clicked')

        refresh_gui(0)

        tomate_session.reset.assert_called_once_with()
