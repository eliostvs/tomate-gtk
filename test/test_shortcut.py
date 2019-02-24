from unittest import mock

import pytest
from wiring import SingletonScope
from wiring.scanning import scan_to_graph


@pytest.fixture
def shortcut_manager(mocker, config):
    mocker.patch("tomate_gtk.shortcut.Gtk.AccelMap.add_entry")
    mocker.patch("tomate_gtk.shortcut.Gtk.AccelMap.change_entry")

    from gi.repository import Gtk
    from tomate_gtk.shortcut import ShortcutManager

    return ShortcutManager(config, mock.Mock(Gtk.AccelGroup))


@pytest.mark.parametrize(
    "option, shortcut",
    (["start", "<control>s"], ["stop", "<control>p"], ["reset", "<control>r"]),
)
def test_connect(option, shortcut, shortcut_manager, mocker, config):
    # Given
    from gi.repository import Gtk

    fn = mocker.Mock()
    key, mod = Gtk.accelerator_parse(shortcut)

    def side_effect(section, _option, fallback=None):
        assert section == "shortcuts"
        assert _option == option
        assert fallback == shortcut

        return shortcut

    config.get.side_effect = side_effect
    config.SECTION_SHORTCUTS = "shortcuts"

    # When
    shortcut_manager.connect(option, fn)

    # Then
    shortcut_manager.accel_group.connect_by_path.assert_called_once_with(
        "<Tomate>/accelerators/{}".format(option), fn
    )

    Gtk.AccelMap.add_entry.assert_any_call(
        "<Tomate>/accelerators/{}".format(option), key, mod
    )


def test_change(shortcut_manager):
    # Given
    from gi.repository import Gtk

    shortcut = "<Control>b"
    key, mod = Gtk.accelerator_parse(shortcut)

    # When
    shortcut_manager.change("name", shortcut)

    # Then
    Gtk.AccelMap.change_entry.assert_called_once_with(
        f"<Tomate>/accelerators/name", key, mod, True
    )


def test_initialize(shortcut_manager, mocker, config):
    # Given
    from gi.repository import Gtk

    window = mocker.Mock(Gtk.Window)

    # When
    shortcut_manager.initialize(window)

    # Then
    window.add_accel_group.assert_called_once_with(shortcut_manager.accel_group)


def test_module(graph, mocker, shortcut_manager):
    scan_to_graph(["tomate_gtk.shortcut"], graph)

    assert "view.shortcut" in graph.providers

    graph.register_instance("tomate.config", mocker.Mock())

    provider = graph.providers["view.shortcut"]
    assert provider.scope == SingletonScope

    assert isinstance(graph.get("view.shortcut"), shortcut_manager.__class__)
