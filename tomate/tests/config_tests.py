from __future__ import unicode_literals

import os
import unittest

from mock import Mock, mock_open, patch
from wiring import FactoryProvider, Graph, SingletonScope

BaseDirectory_attrs = {
    'xdg_config_home': '/home/mock/.config',
    'load_data_paths.side_effect': lambda *args: [os.path.join('/usr/mock/', *args)],
}


class TestConfigInterface(unittest.TestCase):

    def test_interface(self):
        from tomate.config import IConfig, Config

        config = Config(Mock(), Mock())
        IConfig.check_compliance(config)


@patch('tomate.config.BaseDirectory', spec_set=True, **BaseDirectory_attrs)
class TestConfig(unittest.TestCase):

    def setUp(self):
        from tomate.config import Config

        self.config = Config(Mock(), Mock())

        self.mo = mock_open()

    def test_get_config_path(self, *args):
        self.assertEqual('/home/mock/.config/tomate/tomate.conf', self.config.get_config_path())

    def test_get_plugin_path(self, *args):
        self.assertEqual(['/usr/mock/tomate/plugins'], self.config.get_plugin_paths())

    def test_write_config(self, *args):
        with patch('tomate.config.open', self.mo, create=True):
            self.config.save()

        self.assertTrue(self.config.parser.write.called)
        self.config.parser.write.assert_called_once_with(self.mo())

    @patch('tomate.config.os.path.exists', spec_set=True, return_value=True)
    def test_get_media_file(self, mpath, *args):
        self.assertEqual('file:///usr/mock/tomate/media/alarm.mp3', self.config.get_media_uri('alarm.mp3'))

    def test_get_resource_path_should_raise_exception(self, *args):
        self.assertRaises(EnvironmentError, self.config.get_resource_path, '/file/not/exist/')

    @patch('tomate.config.IconTheme.getIconPath', return_value=None)
    def test_get_icon_path_should_raise_exception(self, mgetIconPath, *args):
        self.assertRaises(EnvironmentError, self.config.get_icon_path, 'tomate', 22)

    @patch('tomate.config.IconTheme.getIconPath', spec_set=True)
    def test_get_icon_path_should_success(self, mgetIconPath, *args):
        mgetIconPath.side_effect = (
            lambda name, size, theme, extensions:
            '/usr/mock/icons/hicolor/{size}x{size}/apps/{name}.png'
            .format(name=name, size=size)
        )

        self.assertEqual('/usr/mock/icons/hicolor/22x22/apps/tomate.png',
                         self.config.get_icon_path('tomate', 22))

    def test_icon_paths_should_success(self, *args):
        self.assertEqual(['/usr/mock/icons'], self.config.get_icon_paths())

    def test_get_option(self, *args):
        self.config.parser.has_section.return_value = False
        self.config.parser.has_option.return_value = False
        self.config.parser.get.return_value = '25'
        self.config.parser.getint.return_value = 25

        self.assertEqual(25, self.config.get_int('Timer', 'pomodoro duration'))

        self.config.parser.has_section.assert_called_once_with('timer')

        self.config.parser.add_section.assert_called_once_with('timer')

        self.config.parser.has_option.assert_called_once_with('timer', 'pomodoro_duration')

        self.config.parser.get.assert_called_once_with('timer', 'pomodoro_duration')

        self.config.parser.set.assert_called_once_with('timer', 'pomodoro_duration', '25')

    def test_get_options(self, *args):
        self.config.get('section', 'option')
        self.config.parser.get.assert_called_with('section', 'option')

        self.config.get_int('section', 'option')
        self.config.parser.getint.assert_called_with('section', 'option')

    def test_set_option(self, *args):
        self.config.parser.has_section.return_value = False

        with patch('tomate.config.open', self.mo, create=True):
            self.config.set('Timer', 'Shortbreak Duration', 4)

            self.config.parser.has_section.assert_called_once_with('timer')
            self.config.parser.add_section.assert_called_once_with('timer')
            self.config.parser.set.assert_called_once_with('timer', 'shortbreak_duration', 4)

            self.config.parser.write.assert_called_once_with(self.mo())


@patch('tomate.config.BaseDirectory', spec_set=True, **BaseDirectory_attrs)
class TestConfigSignals(unittest.TestCase):

    def setUp(self, *args):
        from tomate.config import Config

        self.config = Config(Mock(), Mock())

        self.mo = mock_open()

    def test_should_emit_setting_changed(self, *args):
        with patch('tomate.config.open', self.mo, create=True):
            self.config.set('Timer', 'Pomodoro', 4)

            self.config.signals.emit.assert_called_once_with('setting_changed',
                                                             section='timer',
                                                             option='pomodoro',
                                                             value=4)


class TestConfigModule(unittest.TestCase):

    def test_module(self):
        from tomate.config import Config, ConfigProvider

        graph = Graph()

        self.assertEqual(['tomate.config'], ConfigProvider.providers.keys())
        ConfigProvider().add_to(graph)

        self.assertIn('config.parser', graph.providers.keys())

        provider = graph.providers['tomate.config']

        self.assertIsInstance(provider, FactoryProvider)
        self.assertEqual(provider.scope, SingletonScope)
        self.assertEqual(provider.dependencies,
                         dict(parser='config.parser', signals='tomate.signals'))

        graph.register_instance('tomate.signals', Mock())
        self.assertIsInstance(graph.get('tomate.config'), Config)
