import pytest
from gi.repository import Gtk
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.widgets import InfoBar

SPECIFICATION = 'view.infobar'


@pytest.fixture
def infobar():
    return InfoBar()


def test_taskbutton_module(graph):
    from tomate_gtk.widgets.infobar import InfoBar

    scan_to_graph(['tomate_gtk.widgets.infobar'], graph)

    assert SPECIFICATION in graph.providers

    provider = graph.providers[SPECIFICATION]

    assert provider.scope == SingletonScope

    assert isinstance(graph.get(SPECIFICATION), InfoBar)


def test_show_message(infobar):
    infobar.show_message('foo', Gtk.MessageType.WARNING)

    assert infobar.label.get_text() == 'foo'
    assert infobar.get_message_type() == Gtk.MessageType.WARNING


def test_clear_message(infobar):
    infobar.show_message('foo', Gtk.MessageType.WARNING)

    infobar.clear_message_and_hide()

    assert infobar.label.get_text() == ''


def test_get_widget(infobar):
    assert infobar.widget == infobar


def test_hide_message_after_some_time(mocker):
    with mocker.patch('tomate_gtk.widgets.infobar') as mock_glib:
        from tomate_gtk.widgets.infobar import SECONDS_TO_HIDE
        infobar = InfoBar()

        infobar.show_message('foo', Gtk.MessageType.INFO)

        assert infobar.label.get_text() == 'foo'
        assert infobar.get_message_type() == Gtk.MessageType.INFO

        mock_glib.timeout_add_seconds(SECONDS_TO_HIDE, infobar.clear_message_and_hide)
