from typing import Protocol
from uuid import uuid4


class IDFactory(Protocol):
    def new(self) -> str: ...


class UUIDFactory:
    def new(self) -> str:
        return str(uuid4())
