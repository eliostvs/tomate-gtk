from datetime import datetime, timezone
from typing import Protocol

from wiring import SingletonScope
from wiring.scanning import register


class Clock(Protocol):
    def now(self) -> datetime: ...


@register.factory("tomate.clock", scope=SingletonScope)
class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
