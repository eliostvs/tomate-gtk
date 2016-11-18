from __future__ import unicode_literals

from mock import Mock
from tomate.graph import graph

from tomate_gtk.dialogs.preference import (ExtensionStack, PreferenceDialog,
                                           TimerDurationStack)


def test_preference_module():
    config = Mock(**{'get_int.return_value': 25})
    graph.register_instance('tomate.config', config)
    graph.register_factory('tomate.plugin', Mock)
    graph.register_factory('view.preference.extension', ExtensionStack)
    graph.register_factory('view.preference.duration', TimerDurationStack)

    # Extension Stack
    provider = graph.providers['view.preference.extension']

    assert provider.dependencies == {'config': 'tomate.config', 'plugin': 'tomate.plugin'}

    # Duration Stack
    provider = graph.providers['view.preference.duration']

    assert provider.dependencies == {'config': 'tomate.config'}

    # Preference Dialog
    provider = graph.providers['view.preference']

    assert provider.dependencies == {'extension': 'view.preference.extension',
                                     'duration': 'view.preference.duration'}

    preference = graph.get('view.preference')
    assert isinstance(preference, PreferenceDialog)
