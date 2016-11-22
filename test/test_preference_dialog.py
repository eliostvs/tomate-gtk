from __future__ import unicode_literals

from mock import Mock
from wiring import SingletonScope

from tomate_gtk.dialogs.preference import (ExtensionStack, PreferenceDialog,
                                           TimerDurationStack)


def test_preference_extension_module(graph, config):
    assert 'view.preference.extension' in graph.providers

    provider = graph.providers['view.preference.extension']

    assert provider.scope == SingletonScope
    assert isinstance(graph.get('view.preference.extension'), ExtensionStack)


def test_preference_duration_module(graph):
    assert 'view.preference.duration' in graph.providers

    provider = graph.providers['view.preference.duration']

    assert provider.scope == SingletonScope
    assert isinstance(graph.get('view.preference.duration'), TimerDurationStack)


def test_preference_module(graph, config):
    assert 'view.preference' in graph.providers

    provider = graph.providers['view.preference']

    assert provider.scope == SingletonScope

    graph.register_instance('tomate.config', config)
    graph.register_factory('tomate.plugin', Mock)
    graph.register_factory('view.preference.extension', ExtensionStack)
    graph.register_factory('view.preference.duration', TimerDurationStack)

    assert isinstance(graph.get('view.preference'), PreferenceDialog)
