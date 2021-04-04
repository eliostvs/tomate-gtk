import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate import __version__


@pytest.fixture
def subject(graph, config):
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.ui.dialogs.about"], graph)

    return graph.get("tomate.ui.about")


def test_module(graph, subject):
    assert graph.get("tomate.ui.about") is subject


def test_dialog_info(subject):
    assert subject.get_comments() == "Tomate Pomodoro Timer (GTK+ Interface)"
    assert subject.get_copyright() == "2014, Elio Esteves Duarte"
    assert subject.get_version() == __version__
    assert subject.get_website() == "https://github.com/eliostvs/tomate-gtk"
    assert subject.get_website_label() == "Tomate GTK on Github"
    assert subject.get_license_type() == Gtk.License.GPL_3_0
    assert subject.get_logo() is not None


def test_close_dialog(subject, mocker):
    subject.hide = mocker.Mock()

    subject.emit("response", 0)
    refresh_gui()

    subject.hide.assert_called_once()
