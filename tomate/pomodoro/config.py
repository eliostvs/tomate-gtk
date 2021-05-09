import logging
import os
from collections import namedtuple
from configparser import RawConfigParser
from typing import List, Union

from wiring import SingletonScope, inject
from wiring.scanning import register
from xdg import BaseDirectory, IconTheme

from .event import Bus, Events

logger = logging.getLogger(__name__)

Payload = namedtuple("ConfigPayload", "action section option value")


@register.factory("tomate.config", scope=SingletonScope)
class Config:
    APP_NAME = "tomate"
    SHORTCUT_SECTION = "shortcuts"
    DURATION_SECTION = "timer"
    DURATION_LONG_BREAK = "longbreak_duration"
    DURATION_POMODORO = "pomodoro_duration"
    DURATION_SHORT_BREAK = "shortbreak_duration"
    DEFAULTS = {
        DURATION_POMODORO: "25",
        DURATION_SHORT_BREAK: "5",
        DURATION_LONG_BREAK: "15",
        "long_break_interval": "4",
    }

    @inject(bus="tomate.bus")
    def __init__(self, bus: Bus, parser=RawConfigParser(defaults=DEFAULTS, strict=True)):
        self.parser = parser
        self._bus = bus
        self.load()

    def __getattr__(self, attr):
        return getattr(self.parser, attr)

    def load(self) -> None:
        logger.debug("action=load uri=%s", self.config_path())

        self.parser.read(self.config_path())

    def save(self) -> None:
        logger.debug("action=write uri=%s", self.config_path())

        with open(self.config_path(), "w") as f:
            self.parser.write(f)

    def config_path(self) -> str:
        BaseDirectory.save_config_path(self.APP_NAME)
        return os.path.join(BaseDirectory.xdg_config_home, self.APP_NAME, self.APP_NAME + ".conf")

    def media_uri(self, *resources: str) -> str:
        return "file://" + self._resource_path(self.APP_NAME, "media", *resources)

    def plugin_paths(self) -> List[str]:
        return remove_duplicates(self._load_data_paths(self.APP_NAME, "plugins"))

    def icon_paths(self) -> List[str]:
        return remove_duplicates(self._load_data_paths("icons"))

    def _resource_path(self, *resources) -> str:
        for resource in self._load_data_paths(*resources):
            if os.path.exists(resource):
                return resource

        raise EnvironmentError("Resource '%s' not found!" % resources[-1])

    def _load_data_paths(self, *resources) -> List[str]:
        return [path for path in BaseDirectory.load_data_paths(*resources)]

    def icon_path(self, iconname, size=None, theme=None) -> str:
        icon_path = IconTheme.getIconPath(iconname, size, theme, extensions=["png", "svg", "xpm"])

        if icon_path is not None:
            return icon_path

        raise EnvironmentError("Icon '%s' not found!" % iconname)

    def get_int(self, section: str, option: str, fallback=None) -> int:
        return self.get(section, option, fallback, method="getint")

    def get_bool(self, section: str, option: str, fallback=None) -> bool:
        return self.get(section, option, fallback, method="getboolean")

    def get(self, section: str, option: str, fallback=None, method="get") -> Union[str, int, bool]:
        section = self.normalize(section)
        option = self.normalize(option)
        if not self.parser.has_section(section):
            self.parser.add_section(section)

        logger.debug("action=get section=%s option=%s", section, option)

        return getattr(self.parser, method)(section, option, fallback=fallback)

    def set(self, section: str, option: str, value) -> None:
        section = self.normalize(section)
        option = self.normalize(option)
        if not self.parser.has_section(section):
            self.parser.add_section(section)

        self.parser.set(section, option, value)
        self.save()

        logger.debug("action=set section=%s option=%s value=%s", section, option, value)
        self._bus.send(
            Events.CONFIG_CHANGE,
            payload=Payload(action="set", section=section, option=option, value=value),
        )

    def remove(self, section, option) -> None:
        section = self.normalize(section)
        option = self.normalize(option)
        self.parser.remove_option(section, option)

        payload = Payload(action="remove", section=section, option=option, value="")
        self._bus.send(section, payload=payload)

        logger.debug("action=remove section=%s option=%s", section, option)

    @staticmethod
    def normalize(name: str) -> str:
        return name.replace(" ", "_").lower()


def remove_duplicates(original: List[str]) -> List[str]:
    return list(set(original))
