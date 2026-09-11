import logging
import os
from collections import namedtuple
from configparser import RawConfigParser
from typing import ClassVar, cast

from wiring import SingletonScope, inject
from wiring.scanning import register
from xdg import BaseDirectory, IconTheme

from .event import Bus, Events

logger = logging.getLogger(__name__)

ConfigPayload = namedtuple("ConfigPayload", "action section option value")


@register.factory("tomate.config", scope=SingletonScope)
class Config:
    APP_NAME = "tomate"
    SHORTCUT_SECTION = "shortcuts"
    DURATION_SECTION = "timer"
    DURATION_LONG_BREAK = "longbreak_duration"
    DURATION_POMODORO = "pomodoro_duration"
    DURATION_SHORT_BREAK = "shortbreak_duration"
    DEFAULTS: ClassVar[dict[str, str]] = {
        DURATION_POMODORO: "25",
        DURATION_SHORT_BREAK: "5",
        DURATION_LONG_BREAK: "15",
        "long_break_interval": "4",
    }

    @inject(bus="tomate.bus")
    def __init__(self, bus: Bus, parser=None):
        if parser is None:
            parser = RawConfigParser(defaults=self.DEFAULTS, strict=True)

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

    def plugin_paths(self) -> list[str]:
        return remove_duplicates(self._load_data_paths(self.APP_NAME, "plugins"))

    def icon_paths(self) -> list[str]:
        return remove_duplicates(self._load_data_paths("icons"))

    def _resource_path(self, *resources) -> str:
        for resource in self._load_data_paths(*resources):
            if os.path.exists(resource):
                return resource

        raise OSError(f"Resource '{resources[-1]}' not found!")

    def _load_data_paths(self, *resources) -> list[str]:
        return [path for path in BaseDirectory.load_data_paths(*resources)]

    def icon_path(self, iconname, size=None, theme=None) -> str:
        icon_path = IconTheme.getIconPath(iconname, size, theme, extensions=["png", "svg", "xpm"])

        if icon_path is not None:
            return icon_path

        raise OSError(f"Icon '{iconname}' not found!")

    def get_int(self, section: str, option: str, fallback: int | None = None) -> int:
        section, option = self._prepare_option(section, option)
        return cast(int, self.parser.getint(section, option, fallback=fallback))

    def get_bool(self, section: str, option: str, fallback: bool | None = None) -> bool:
        section, option = self._prepare_option(section, option)
        return cast(bool, self.parser.getboolean(section, option, fallback=fallback))

    def get_float(self, section: str, option: str, fallback: float | None = None) -> float:
        section, option = self._prepare_option(section, option)
        return cast(float, self.parser.getfloat(section, option, fallback=fallback))

    def get(self, section: str, option: str, fallback: str | None = None) -> str:
        section, option = self._prepare_option(section, option)
        return cast(str, self.parser.get(section, option, fallback=fallback))

    def _prepare_option(self, section: str, option: str) -> tuple[str, str]:
        section = self.normalize(section)
        option = self.normalize(option)
        if not self.parser.has_section(section):
            self.parser.add_section(section)

        logger.debug("action=get section=%s option=%s", section, option)
        return section, option

    def set(self, section: str, option: str, value) -> None:
        logger.debug("action=set section=%s option=%s value=%s", section, option, value)

        section = self.normalize(section)
        option = self.normalize(option)
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, option, value)
        self.save()

        payload = ConfigPayload(action="set", section=section, option=option, value=value)
        self._bus.publish(Events.CONFIG_CHANGE, payload=payload)

    def remove(self, section, option) -> None:
        logger.debug("action=remove section=%s option=%s", section, option)

        section = self.normalize(section)
        option = self.normalize(option)
        self.parser.remove_option(section, option)
        self.save()

        payload = ConfigPayload(action="remove", section=section, option=option, value="")
        self._bus.publish(Events.CONFIG_CHANGE, payload=payload)

    @staticmethod
    def normalize(name: str) -> str:
        return name.replace(" ", "_").lower()


def remove_duplicates(original: list[str]) -> list[str]:
    return list(set(original))
