from unittest.mock import Mock

import pytest

from cs_events import Event, events
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


def test_events_field() -> None:
    @events
    class TestClass:
        event1: Event[[]]

    assert isinstance(TestClass().event1, Event)


def test_events_field_init() -> None:
    @events
    class TestClass0:
        no_events: None

    assert "__init__" not in vars(TestClass0)

    __init__ = Mock()

    @events
    class TestClass1:
        event1: Event[[]]

        def __init__(self) -> None:
            __init__(self)

    obj1 = TestClass1()
    __init__.assert_called_once_with(obj1)
    assert isinstance(obj1.event1, Event)

    @events
    class TestClass2(TestClass1):
        event2: Event[[]]

    __init__.reset_mock()
    obj2 = TestClass2()
    __init__.assert_called_once_with(obj2)
    assert isinstance(obj2.event1, Event)
    assert isinstance(obj2.event2, Event)


def test_events_prefix() -> None:
    @events(prefix="on_")
    class TestClass:
        event1: Event[[]]
        on_event2: Event[[]]

    obj = TestClass()

    with pytest.raises(AttributeError, match="'TestClass' object has no attribute 'event1'"):
        obj.event1
    assert isinstance(obj.on_event2, Event)


def test_events_properties() -> None:
    @events(properties=True)
    class TestClass:
        event1: Event[int]
        event2: Event[str, str]
        event3: Event[...]

        def __init__(self) -> None:
            self._events = {}

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
