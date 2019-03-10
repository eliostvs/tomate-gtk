import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph

from tests.conftest import refresh_gui
from tomate.ui.dialogs import AboutDialog


@pytest.fixture
def subject(mock_config):
    return AboutDialog(mock_config)


def test_module(graph, mock_config):
    spec = "tomate.ui.about"
    package = "tomate.ui.dialogs.about"

    graph.register_instance("tomate.config", mock_config)
    scan_to_graph([package], graph)

    assert spec in graph.providers

    provider = graph.providers[spec]
    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), AboutDialog)


def test_response(subject, mocker):
    # given
    subject.hide = mocker.Mock()

    # when
    subject.emit("response", 0)
    refresh_gui()

    # then
    subject.hide.assert_called_once()
