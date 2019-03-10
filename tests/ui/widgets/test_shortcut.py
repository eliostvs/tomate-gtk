from unittest import mock

import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph


@pytest.fixture
def subject(mocker, mock_config):
    mocker.patch("tomate.ui.shortcut.Gtk.AccelMap.add_entry")
    mocker.patch("tomate.ui.shortcut.Gtk.AccelMap.change_entry")

    from gi.repository import Gtk
    from tomate.ui.shortcut import ShortcutManager

    return ShortcutManager(mock_config, mock.Mock(Gtk.AccelGroup))


def test_label(subject, mock_config):
    # given
    shortcut_name = "start"
    shortcut = "<control>s"

    def side_effect(section, option, fallback=None):
        assert section == "shortcuts"
        assert option == shortcut_name
        assert fallback == shortcut

        return shortcut

    mock_config.get.side_effect = side_effect

    # when
    label = subject.label(shortcut_name)

    # then
    assert label == "Ctrl+S"


@pytest.mark.parametrize(
    "option, shortcut",
    (["start", "<control>s"], ["stop", "<control>p"], ["reset", "<control>r"]),
)
def test_connect(option, shortcut, subject, mocker, mock_config):
    # given
    from gi.repository import Gtk

    fn = mocker.Mock()
    key, mod = Gtk.accelerator_parse(shortcut)

    def side_effect(section, _option, fallback=None):
        assert section == "shortcuts"
        assert _option == option
        assert fallback == shortcut

        return shortcut

    mock_config.get.side_effect = side_effect

    # when
    subject.connect(option, fn)

    # then
    subject.accel_group.connect_by_path.assert_called_once_with(
        "<tomate>/Global/{}".format(option), fn
    )

    Gtk.AccelMap.add_entry.assert_any_call(
        "<tomate>/Global/{}".format(option), key, mod
    )


def test_change(subject):
    # given
    from gi.repository import Gtk

    shortcut = "<Control>b"
    key, mod = Gtk.accelerator_parse(shortcut)

    # when
    subject.change("name", shortcut)

    # then
    Gtk.AccelMap.change_entry.assert_called_once_with(
        "<tomate>/Global/name", key, mod, True
    )


def test_initialize(subject, mocker):
    # given
    from gi.repository import Gtk

    window = mocker.Mock(Gtk.Window)

    # when
    subject.initialize(window)

    # then
    window.add_accel_group.assert_called_once_with(subject.accel_group)


def test_module(graph, mocker, subject):
    spec = "tomate.ui.shortcut"
    package = "tomate.ui.shortcut"

    scan_to_graph([package], graph)

    assert spec in graph.providers

    graph.register_instance("tomate.config", mocker.Mock())

    provider = graph.providers[spec]
    assert provider.scope == SingletonScope

    assert isinstance(graph.get(spec), subject.__class__)
