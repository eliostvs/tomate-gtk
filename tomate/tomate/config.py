from __future__ import unicode_literals

import logging
import os

from wiring import (implements, inject, Interface, Module, provides, scope,
                    SingletonScope)
from xdg import BaseDirectory, IconTheme

logger = logging.getLogger(__name__)

DEFAULTS = {
    'pomodoro_duration': '25',
    'shortbreak_duration': '5',
    'longbreak_duration': '15',
    'long_break_interval': '4',
}


class IConfig(Interface):
    app_name = ''

    def get_config_path():
        pass

    def get_resource_paths(*resources):
        pass

    def get_resource_path(*resources):
        pass

    def get_plugin_paths():
        pass

    def get_icon_paths():
        pass

    def get_icon_path(iconname, size=None, theme=None):
        pass

    def get_media_uri(*resources):
        pass

    def get(section, option):
        pass

    def get_int(section, option):
        pass

    def set(section, option, value):
        pass

    def load():
        pass

    def save():
        pass


@implements(IConfig)
class Config(object):

    app_name = 'tomate'

    @inject(parser='config.parser', signals='tomate.signals')
    def __init__(self, parser, signals):
        self.parser = parser
        self.signals = signals

        self.load()

    def load(self):
        logger.debug('load config file %s', self.get_config_path())

        self.parser.read(self.get_config_path())

    def save(self):
        logger.debug('writing config file %s', self.get_config_path())

        with open(self.get_config_path(), 'w') as f:
            self.parser.write(f)

    def get_config_path(self):
        BaseDirectory.save_config_path(self.app_name)
        return os.path.join(BaseDirectory.xdg_config_home, self.app_name, self.app_name + '.conf')

    def get_media_uri(self, *resources):
        return 'file://' + self.get_resource_path(self.app_name, 'media', *resources)

    def get_plugin_paths(self):
        return self.get_resource_paths(self.app_name, 'plugins')

    def get_icon_paths(self):
        return self.get_resource_paths('icons')

    def get_resource_path(self, *resources):
        for resource in self.get_resource_paths(*resources):
            if os.path.exists(resource):
                return resource

            logger.debug('resource not found: %s', resource)

        raise EnvironmentError('resource with path %s not found!' % os.path.join(*resources))

    def get_resource_paths(self, *resources):
        return [p for p in BaseDirectory.load_data_paths(*resources)]

    def get_icon_path(self, iconname, size=None, theme=None):
        iconpath = IconTheme.getIconPath(iconname, size, theme, extensions=['png', 'svg', 'xpm'])

        if iconpath is not None:
            return iconpath

        raise EnvironmentError('Icon %s not found!' % iconpath)

    def get_int(self, section, option):
        return self._get(section, option, 'getint')

    def get(self, section, option):
        return self._get(section, option)

    def _get(self, section, option, method='get'):
        section = Config.normalize(section)
        option = Config.normalize(option)

        if not self.parser.has_section(section):
            self.parser.add_section(section)

        if not self.parser.has_option(section, option):
            value = self.parser.get(section, option)

            self.parser.set(section, option, value)

        return getattr(self.parser, method)(section, option)

    def set(self, section, option, value):
        section = Config.normalize(section)
        option = Config.normalize(option)

        logger.debug('change setting: s=%s o=%s v=%s', section, option, value)

        if not self.parser.has_section(section):
            self.parser.add_section(section)

        self.parser.set(section, option, value)

        self.save()

        self.signals.emit('setting_changed',
                          section=section,
                          option=option,
                          value=value)

    @staticmethod
    def normalize(name):
        return name.replace(' ', '_').lower()


class ConfigProvider(Module):

    factories = {
        'tomate.config': (Config, SingletonScope)
    }

    @provides('config.parser')
    @scope(SingletonScope)
    def provide_parser(self):
        from ConfigParser import SafeConfigParser

        return SafeConfigParser(DEFAULTS)
