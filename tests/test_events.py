from unittest.mock import Mock

import pytest

from cs_events import Event, EventHandlerCollection, EventHandlerList, event, events


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


def test_events_field_prefix() -> None:
    @events(prefix="on_")
    class TestClass:
        event1: Event[[]]
        on_event2: Event[[]]

    obj = TestClass()

    with pytest.raises(AttributeError, match="'TestClass' object has no attribute 'event1'"):
        obj.event1
    assert isinstance(obj.on_event2, Event)


def test_events_properties() -> None:
    @events(collection="__events", prefix="event")
    class TestClass:
        event1: event[int]
        event2: event[str, str]
        event3: event[...]

        def __init__(self) -> None:
            self.__events = EventHandlerList()

        @property
        def events(self) -> EventHandlerCollection:
            return self.__events

    assert isinstance(TestClass.event1, event)
    assert isinstance(TestClass.event2, event)
    assert isinstance(TestClass.event3, event)

    obj = TestClass()

    assert isinstance(obj.event1, event)
    assert isinstance(obj.event2, event)
    assert isinstance(obj.event3, event)

    assert obj.events["1"] is None
    assert obj.events["2"] is None
    assert obj.events["3"] is None

    def event1_handler(_: int) -> None: ...
    def event2_handler(_0: str, _1: str) -> None: ...

    obj.event1 += event1_handler

    assert (e := obj.events["1"]) is not None
    assert len(e) == 1
    assert obj.events["2"] is None
    assert obj.events["3"] is None

    obj.event1 -= event1_handler

    assert (e := obj.events["1"]) is not None
    assert len(e) == 0
    assert obj.events["2"] is None
    assert obj.events["3"] is None

    obj.event2 -= event2_handler

    assert (e := obj.events["1"]) is not None
    assert len(e) == 0
    assert obj.events["2"] is None
    assert obj.events["3"] is None

    obj.event2 += event2_handler

    assert (e := obj.events["1"]) is not None
    assert len(e) == 0
    assert (e := obj.events["2"]) is not None
    assert len(e) == 1
    assert obj.events["3"] is None