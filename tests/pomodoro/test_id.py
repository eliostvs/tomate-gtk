import uuid

import pytest

from tests.conftest import TestIDFactory
from tomate.pomodoro import IDFactory


def test_uuid_factory_creates_a_string_uuid():
    from tomate.pomodoro.id import UUIDFactory

    value = UUIDFactory().new()

    assert isinstance(value, str)
    assert uuid.UUID(value).version == 4


def test_id_factory_protocol_describes_test_id_factory():
    def create(factory: IDFactory) -> str:
        return factory.new()

    assert create(TestIDFactory("event-id")) == "event-id"


def test_test_id_factory_returns_ids_in_order():
    factory = TestIDFactory("first", "second")

    assert factory.new() == "first"
    assert factory.new() == "second"

    with pytest.raises(StopIteration):
        factory.new()
