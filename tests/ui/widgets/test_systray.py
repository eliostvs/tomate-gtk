import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.pomodoro import State
from tomate.pomodoro.event import Events, connect_events
from tomate.ui.widgets import TrayIconMenu


@pytest.fixture
def subject(mock_view):
    mock_view.widget.get_visible.return_value = False

    Events.View.receivers.clear()

    instance = TrayIconMenu(mock_view)
    connect_events(instance)

    return instance


def test_show_window_when_show_item_is_clicked(mock_view, subject):
    # given
    subject._show_item.activate()

    # when
    refresh_gui()

    # then
    mock_view.show.assert_called_once_with()


def test_change_items_visibility_when_window_is_show(subject, mock_view):
    # when
    Events.View.send(State.showed)

    # then
    assert subject._hide_item.get_visible()
    assert not subject._show_item.get_visible()


def test_hide_window_when_hide_item_is_clicked(mock_view, subject):
    # give
    subject._hide_item.activate()

    # when
    refresh_gui()

    # then
    mock_view.hide.assert_called_once_with()


def test_change_items_visibility_when_window_is_hide(subject, mock_view):
    # when
    Events.View.send(State.hid)

    # then
    assert not subject._hide_item.get_visible()
    assert subject._show_item.get_visible()


def test_module(graph, mock_view):
    spec = "tomate.ui.tray.menu"
    package = "tomate.ui.widgets.systray"

    graph.register_instance("tomate.ui.view", mock_view)

    scan_to_graph([package], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]

    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), TrayIconMenu)
