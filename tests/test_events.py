from typing import cast
from unittest.mock import Mock

from events import (AsyncEvent, Event, EventHandlerCollection, EventHandlerList, async_event, event,
                    event_key, events,)


def test_events_field() -> None:
    @events
    class TestClass:
        event1: Event[[]]
        event2: AsyncEvent[[]]

    assert isinstance(TestClass().event1, Event)
    assert isinstance(TestClass().event2, AsyncEvent)


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


def test_events_properties() -> None:
    @events(collection="__events")
    class TestClass:
        event1: event[int]
        event2: event[str, str]
        event3: event[...]
        event4: async_event[bool]

        def __init__(self) -> None:
            self.__events = EventHandlerList()

        @property
        def events(self) -> EventHandlerCollection:
            return self.__events

    assert isinstance(TestClass.event1, event)
    assert isinstance(TestClass.event2, event)
    assert isinstance(TestClass.event3, event)
    assert isinstance(TestClass.event4, async_event)

    obj = TestClass()

    assert isinstance(obj.event1, event)
    assert isinstance(obj.event2, event)
    assert isinstance(obj.event3, event)
    assert isinstance(obj.event4, async_event)

    assert obj.events["event1"] is None
    assert obj.events["event2"] is None
    assert obj.events["event3"] is None
    assert obj.events["event4"] is None

    def event1_handler(_: int) -> None: ...
    def event2_handler(_: str, __: str) -> None: ...
    async def event4_handler(_: bool) -> None: ...

    obj.event1 += event1_handler

    assert (e := obj.events["event1"]) is not None
    assert len(e) == 1
    assert obj.events["event2"] is None
    assert obj.events["event3"] is None
    assert obj.events["event4"] is None

    obj.event1 -= event1_handler

    assert (e := obj.events["event1"]) is not None
    assert len(e) == 0
    assert obj.events["event2"] is None
    assert obj.events["event3"] is None
    assert obj.events["event4"] is None

    obj.event2 -= event2_handler

    assert (e := obj.events["event1"]) is not None
    assert len(e) == 0
    assert obj.events["event2"] is None
    assert obj.events["event3"] is None
    assert obj.events["event4"] is None

    obj.event2 += event2_handler

    assert (e := obj.events["event1"]) is not None
    assert len(e) == 0
    assert (e := obj.events["event2"]) is not None
    assert len(e) == 1
    assert obj.events["event3"] is None
    assert obj.events["event4"] is None

    obj.event4 += event4_handler

    assert (e := obj.events["event1"]) is not None
    assert len(e) == 0
    assert (e := obj.events["event2"]) is not None
    assert len(e) == 1
    assert obj.events["event3"] is None
    assert (e := obj.events["event4"]) is not None
    assert len(e) == 1
    assert isinstance(e, AsyncEvent)

    event3_handler1 = Mock()
    event3_handler2 = Mock()
    obj.event3 += event3_handler1
    obj.event3 += event3_handler2

    assert (e := obj.events["event3"]) is not None
    assert list(e) == [event3_handler1, event3_handler2]

    obj.events.invoke("event3", 83261, "hi", [0, False], a=1, b=None)

    event3_handler1.assert_called_once_with(83261, "hi", [0, False], a=1, b=None)
    event3_handler2.assert_called_once_with(83261, "hi", [0, False], a=1, b=None)


def test_events_properties_collection() -> None:
    @events
    class Test:
        e: event[[]]
        events: EventHandlerList

    obj = Test()
    obj.events = cast(EventHandlerList, Mock())

    obj.e += lambda: 0
    cast(Mock, obj.events.add_handler).assert_called_once()

    @events(collection="events2")
    class Test2:
        e: event[[]]
        events: EventHandlerList
        events2: object

    obj2 = Test2()
    obj2.events = cast(EventHandlerList, Mock())
    obj2.events2 = cast(EventHandlerList, Mock())

    obj2.e += lambda: 0
    cast(Mock, obj2.events.add_handler).assert_not_called()
    cast(Mock, obj2.events2.add_handler).assert_called_once()


def test_events_properties_private() -> None:
    @events(collection="__events")
    class _Test:
        e: event[[]]

        def __init__(self) -> None:
            self.__events = EventHandlerList()

    _Test().e += lambda: None

    @events(collection="__events")
    class __Test:
        e: event[[]]

        def __init__(self) -> None:
            self.__events = EventHandlerList()

    __Test().e += lambda: None

    @events
    class _Test_:
        e: event[[]]
        __events: EventHandlerList

        def __init__(self) -> None:
            self.__events = EventHandlerList()

    _Test_().e += lambda: None


def test_events_properties_key() -> None:
    @events
    class Test:
        test1: event[[]] = event_key(_event_test1 := object())
        test2: event[str] = event_key(_event_test2 := object())
        events: EventHandlerCollection

    t = Test()
    t.events = cast(EventHandlerCollection, Mock())

    def handler1() -> None: ...
    def handler2(_: str) -> None: ...

    t.test1 += handler1
    cast(Mock, t.events.add_handler).assert_called_once_with(Test._event_test1, handler1)

    t.test1 -= handler1
    cast(Mock, t.events.remove_handler).assert_called_once_with(Test._event_test1, handler1)

    t.test2 -= handler2
    cast(Mock, t.events.remove_handler).assert_called_with(Test._event_test2, handler2)

    t.test2 += handler2
    cast(Mock, t.events.add_handler).assert_called_with(Test._event_test2, handler2)
