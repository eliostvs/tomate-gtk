from typing import Protocol


class SessionBus(Protocol):
    def request_name(self, name: str, flags: int) -> int: ...

    def get_object(self, bus_name: str, object_path: str) -> object: ...
