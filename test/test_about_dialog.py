import pytest
from conftest import refresh_gui
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tomate_gtk.dialogs.about import AboutDialog


@pytest.fixture
def subject(config):
    return AboutDialog(config)


def test_module(graph, config):
    spec = "view.about"

    graph.register_instance("tomate.config", config)
    scan_to_graph(["tomate_gtk.dialogs.about"], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]
    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), AboutDialog)


def test_response(config, subject, mocker):
    # given
    subject.hide = mocker.Mock()

    # when
    subject.emit("response", 0)
    refresh_gui()

    # then
    subject.hide.assert_called_once()
