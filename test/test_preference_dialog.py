from __future__ import unicode_literals

from mock import Mock
from tomate.graph import graph
from wiring import FactoryProvider, SingletonScope

from tomate_gtk.dialogs.preference import (ExtensionStack, PreferenceDialog,
                                           PreferenceDialogModule,
                                           TimerDurationStack)


def test_preference_module():
    config = Mock(**{'get_int.return_value': 25})
    graph.register_instance('tomate.config', config)
    graph.register_factory('tomate.plugin', Mock)
    graph.register_factory('view.preference.extension', ExtensionStack)
    graph.register_factory('view.preference.duration', TimerDurationStack)

    providers = [
        'view.preference',
        'view.preference.extension',
        'view.preference.duration',
    ]

    assert PreferenceDialogModule.providers.keys() == providers

    PreferenceDialogModule().add_to(graph)

    # Extension Stack
    provider = graph.providers['view.preference.extension']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope
    assert provider.dependencies == {'config': 'tomate.config', 'plugin': 'tomate.plugin'}

    # Duration Stack
    provider = graph.providers['view.preference.duration']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope
    assert provider.dependencies == {'config': 'tomate.config'}

    # Preference Dialog
    provider = graph.providers['view.preference']

    assert isinstance(provider, FactoryProvider)
    assert provider.scope == SingletonScope
    assert provider.dependencies == {'extension': 'view.preference.extension',
                                     'duration': 'view.preference.duration'}

    preference = graph.get('view.preference')
    assert isinstance(preference, PreferenceDialog)
