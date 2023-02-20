from unittest.mock import Mock

import pytest

from cs_events import Event, EventDispatcher
from cs_events._events import _empty_event


def test_Event() -> None:
    def event_handler() -> None: ...

    event = Event()
    assert len(event) == 0

    event = Event(event_handler)
    assert len(event) == 1


def test_Event_impl_Collection() -> None:
    def event_handler1() -> None: ...
    def event_handler2() -> None: ...

    event = Event(
        event_handler1,
        event_handler2,
    )

    assert event_handler1 in event
    assert event_handler2 in event

    assert list(event) == [event_handler1, event_handler2]

    assert len(event) == 2


def test_Event_add_remove() -> None:
    def handler1() -> None: ...
    def handler2() -> None: ...

    event = Event(handler1)
    assert list(event) == [handler1]

    event += handler2
    assert list(event) == [handler1, handler2]

    event -= handler2
    assert list(event) == [handler1]

    event -= handler2
    assert list(event) == [handler1]

    event += handler2
    event += handler1
    event += handler2
    assert list(event) == [handler1, handler2, handler1, handler2]

    event -= handler1
    assert list(event) == [handler1, handler2, handler2]


def test_Event_invoke() -> None:
    handler1 = Mock()
    handler2 = Mock()

    event = Event(handler1, handler2)
    event(12345, "hello", [True, False], a=0, b=None)

    args, kwargs = (12345, "hello", [True, False]), {"a": 0, "b": None}
    handler1.assert_called_once_with(*args, **kwargs)
    handler2.assert_called_once_with(*args, **kwargs)

def test_EventDispatcher() -> None:
    class TestClass(EventDispatcher):
        event1: Event[int]
        event2: Event[str, str]
        event3: Event[...]

    assert isinstance(TestClass.event1, property)
    assert isinstance(TestClass.event2, property)
    assert isinstance(TestClass.event3, property)

    obj = TestClass()

    assert obj.event1 is _empty_event
    assert obj.event2 is _empty_event
    assert obj.event3 is _empty_event

    def event1_handler(_: int) -> None:
        ...

    obj.event1 += event1_handler

    assert len(obj.event1) == 1
    assert type(obj.event1) is Event
    assert obj.event1 is not _empty_event

    obj.event1 -= event1_handler

    assert len(obj.event1) == 0
    assert type(obj.event1) is Event
    assert obj.event1 is not _empty_event

    del obj.event1

    assert len(obj.event1) == 0
    assert type(obj.event1) is not Event
    assert obj.event1 is _empty_event


def test_EventDispatcher_prefix() -> None:
    class TestClass(EventDispatcher, event_prefix="on_"):
        event1: Event[[]]
        on_event2: Event[[]]

    with pytest.raises(AttributeError, match="type object 'TestClass' has no attribute 'event1'"):
        TestClass.event1
    assert isinstance(TestClass.on_event2, property)


def test_EventDispatcher_del() -> None:
    class TestClass(EventDispatcher, del_empty_event=True):
        event: Event[[]]

    def event_handler() -> None:
        ...

    obj = TestClass()
    assert obj.event is _empty_event

    obj.event += event_handler
    assert obj.event is not _empty_event

    obj.event -= event_handler
    assert obj.event is _empty_event
