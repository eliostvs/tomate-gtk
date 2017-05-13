import pytest
from conftest import refresh_gui
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate.constant import State, Task
from tomate.event import Session, connect_events
from tomate_gtk.widgets.modebutton import ModeButton
from tomate_gtk.widgets.taskbutton import TaskButton


@pytest.fixture
def mock_session(mocker):
    return mocker.Mock()


@pytest.fixture
def task_button(mock_session):
    Session.receivers.clear()

    instance = TaskButton(mock_session)
    connect_events(instance)

    return instance


def test_taskbutton_module(graph, mocker):
    scan_to_graph(['tomate_gtk.widgets.taskbutton'], graph)

    assert 'view.taskbutton' in graph.providers

    provider = graph.providers['view.taskbutton']

    assert provider.scope == SingletonScope

    graph.register_factory('tomate.session', mocker.Mock)

    assert isinstance(graph.get('view.taskbutton'), TaskButton)


def test_button_should_be_a_mode_button_widget(task_button):
    assert isinstance(task_button.widget, ModeButton)


def test_buttons_should_be_activate_when_session_finishes(task_button):
    Session.send(State.finished)

    assert task_button.modebutton.get_sensitive() is True


def test_buttons_should_be_deactivate_when_session_starts(task_button):
    Session.send(State.started)

    assert task_button.modebutton.get_sensitive() is False


def test_buttons_should_be_activate_when_session_stops(task_button):
    Session.send(State.stopped)

    assert task_button.modebutton.get_sensitive() is True


def test_change_button_when_session_finishes(task_button):
    Session.send(State.finished, task=Task.shortbreak)

    assert task_button.modebutton.get_selected() is Task.shortbreak.value
    task_button.session.change_task.assert_called_once_with(task=Task.shortbreak)


def test_change_task_when_modebutton_changes(task_button):
    task_button.modebutton.emit('mode_changed', Task.longbreak.value)

    refresh_gui(0)

    task_button.session.change_task.assert_called_once_with(task=Task.longbreak)
