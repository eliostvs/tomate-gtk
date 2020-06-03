import logging
import os
from collections import namedtuple
from configparser import RawConfigParser

from wiring import inject, SingletonScope
from wiring.scanning import register
from xdg import BaseDirectory, IconTheme

logger = logging.getLogger(__name__)

DEFAULTS = {
    "pomodoro_duration": "25",
    "shortbreak_duration": "5",
    "longbreak_duration": "15",
    "long_break_interval": "4",
}

SettingsPayload = namedtuple("SettingsPayload", "action section option value")


@register.factory("tomate.config", scope=SingletonScope)
class Config:
    APP_NAME = "tomate"
    SECTION_SHORTCUTS = "shortcuts"
    SECTION_TIMER = "timer"

    @inject(dispatcher="tomate.events.setting")
    def __init__(
        self, dispatcher, parser=RawConfigParser(defaults=DEFAULTS, strict=True)
    ):
        self.parser = parser
        self._dispatcher = dispatcher

        self.load()

    def load(self):
        logger.debug("action=load uri=%s", self.get_config_path())

        self.parser.read(self.get_config_path())

    def save(self):
        logger.debug("action=write uri=%s", self.get_config_path())

        with open(self.get_config_path(), "w") as f:
            self.parser.write(f)

    def get_config_path(self):
        BaseDirectory.save_config_path(self.APP_NAME)
        return os.path.join(
            BaseDirectory.xdg_config_home, self.APP_NAME, self.APP_NAME + ".conf"
        )

    def get_media_uri(self, *resources):
        return "file://" + self.get_resource_path(self.APP_NAME, "media", *resources)

    def get_plugin_paths(self):
        return self.load_data_paths(self.APP_NAME, "plugins")

    def get_icon_paths(self):
        return self.load_data_paths("icons")

    def get_resource_path(self, *resources):
        for resource in self.load_data_paths(*resources):
            if os.path.exists(resource):
                return resource

        raise EnvironmentError(
            "Resource with path %s not found!" % os.path.join(*resources)
        )

    def load_data_paths(self, *resources):
        return [path for path in BaseDirectory.load_data_paths(*resources)]

    def get_icon_path(self, iconname, size=None, theme=None):
        icon_path = IconTheme.getIconPath(
            iconname, size, theme, extensions=["png", "svg", "xpm"]
        )

        if icon_path is not None:
            return icon_path

        raise EnvironmentError("Icon %s not found!" % icon_path)

    def get_int(self, section, option):
        return self.get(section, option, "getint")

    def get(self, section, option, method="get", fallback=None):
        section = Config.normalize(section)
        option = Config.normalize(option)

        logger.debug("action=set section=%s option=%s", section, option)

        if not self.parser.has_section(section):
            self.parser.add_section(section)

        return getattr(self.parser, method)(section, option, fallback=fallback)

    def set(self, section, option, value):
        section = Config.normalize(section)
        option = Config.normalize(option)

        logger.debug("action=set section=%s option=%s value=%s", section, option, value)

        if not self.parser.has_section(section):
            self.parser.add_section(section)

        self.parser.set(section, option, value)

        self.save()

        payload = SettingsPayload(
            action="set", section=section, option=option, value=value
        )

        self._dispatcher.send(section, payload=payload)

    @staticmethod
    def normalize(name):
        return name.replace(" ", "_").lower()
