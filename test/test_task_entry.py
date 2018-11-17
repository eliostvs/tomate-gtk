import pytest
from gi.repository import Gtk

from tomate.constant import State
from tomate.event import Session, connect_events
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.widgets import TaskEntry


@pytest.fixture
def mock_session(mocker):
    return mocker.Mock()


@pytest.fixture
def task_entry(mock_session):
    Session.receivers.clear()

    instance = TaskEntry(mock_session)
    connect_events(instance)

    return instance


def test_task_entry_module(graph, mocker):
    scan_to_graph(['tomate_gtk.widgets.task_entry', 'tomate'], graph)

    assert 'view.taskentry' in graph.providers

    provider = graph.providers['view.taskentry']

    assert provider.scope == SingletonScope

    graph.register_factory('tomate.session', mocker.Mock)

    assert isinstance(graph.get('view.taskentry'), TaskEntry)


def test_task_entry_should_be_disable_when_session_starts(task_entry):
    Session.send(State.started)

    assert task_entry.widget.get_sensitive() is False


def test_task_entry_should_be_disable_when_session_stops(task_entry):
    Session.send(State.stopped)

    assert task_entry.widget.get_sensitive() is True


def test_task_entry_should_be_disable_when_session_finishes(task_entry):
    Session.send(State.finished)

    assert task_entry.widget.get_sensitive() is True


def test_reset_entry_lose_focus_when_reset_icon_is_clicked(task_entry, mocker):
    task_entry.widget.get_toplevel = mocker.Mock()
    task_entry.widget.set_text('foo')

    task_entry.widget.emit('icon-press', Gtk.EntryIconPosition(1), None)

    assert task_entry.widget.get_text() == ''
    task_entry.widget.get_toplevel.return_value.set_focus.assert_called_with(None)


def test_update_session_when_task_name_changes(task_entry, mock_session):
    task_entry.widget.set_text('foo')
    task_entry.widget.emit('changed')

    assert mock_session.task_name == 'foo'


def test_disable_reset_icon_and_not_change_session_task_name_when_task_name_is_empty_or_blank(task_entry):
    task_entry.session.task_name = None
    task_entry.widget.set_text(' ')
    task_entry.widget.emit('changed')

    assert task_entry.widget.get_icon_sensitive(1) is False
    assert task_entry.session.task_name is None


def test_enable_reset_icon_when_task_name_is_not_blank(task_entry):
    task_entry.widget.set_text('foo')
    task_entry.widget.emit('changed')

    assert task_entry.widget.get_icon_sensitive(1) is True
    assert task_entry.session.task_name == 'foo'
