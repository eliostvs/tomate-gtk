from unittest.mock import Mock

import pytest

from tomate.core.event import ObservableProperty


class Subject(object):
    function = Mock()

    state = ObservableProperty("a", function, event="spam")
    other_state = ObservableProperty("b", function, "_hide")


@pytest.fixture()
def subject():
    return Subject()


def test_return_initial_value(subject):
    assert "a" == subject.state
    assert "a" == Subject.state


def test_has_default_attribute(subject):
    subject.state = "a"

    assert hasattr(subject, "_state")
    assert "a" == subject.state


def test_has_configurable_attribute(subject):
    subject.other_state = "b"

    assert hasattr(subject, "_hide")
    assert subject.other_state == subject._hide


def test_call_trigger_method_with_chose_event_type(subject):
    subject.state = "a"

    subject.function.assert_called_with(subject, "spam")


def test_call_trigger_method_with_default_event_type(subject):
    subject.other_state = "b"

    subject.function.assert_called_with(subject, "b")
