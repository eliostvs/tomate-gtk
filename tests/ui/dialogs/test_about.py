import pytest
from gi.repository import Gtk
from wiring.scanning import scan_to_graph

from tomate import __version__
from tomate.ui.testing import refresh_gui


@pytest.fixture
def about(graph, config):
    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate.ui.dialogs.about"], graph)

    return graph.get("tomate.ui.about")


def test_module(graph, about):
    assert graph.get("tomate.ui.about") is about


def test_dialog_info(about):
    assert about.get_comments() == "Tomate Pomodoro Timer (GTK+ Interface)"
    assert about.get_copyright() == "2014, Elio Esteves Duarte"
    assert about.get_version() == __version__
    assert about.get_website() == "https://github.com/eliostvs/tomate-gtk"
    assert about.get_website_label() == "Tomate GTK on Github"
    assert about.get_license_type() == Gtk.License.GPL_3_0
    assert about.get_logo() is not None


def test_close_dialog(about, mocker):
    about.hide = mocker.Mock()

    about.emit("response", 0)
    refresh_gui()

    about.hide.assert_called_once()
