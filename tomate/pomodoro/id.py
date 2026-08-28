from typing import Protocol
from uuid import uuid4

from wiring import SingletonScope
from wiring.scanning import register


class IDFactory(Protocol):
    def new(self) -> str: ...


@register.factory("tomate.id_factory", scope=SingletonScope)
class UUIDFactory:
    def new(self) -> str:
        return str(uuid4())
