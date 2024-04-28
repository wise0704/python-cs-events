import asyncio
from collections.abc import Callable
from unittest.mock import Mock

from events import AsyncEvent, Event, async_event, event


def test_Event() -> None:
    def event_handler() -> None: ...

    assert len(Event()) == 0
    assert len(Event(event_handler)) == 1


def test_AsyncEvent() -> None:
    async def event_handler() -> None: ...

    assert len(AsyncEvent()) == 0
    assert len(AsyncEvent(event_handler)) == 1


def test_Event_impl_Collection() -> None:
    def handler1() -> None: ...
    def handler2() -> None: ...

    e = Event(
        handler1,
        handler2,
    )

    assert handler1 in e
    assert handler2 in e

    assert list(e) == [handler1, handler2]

    assert len(e) == 2


def test_AsyncEvent_impl_Collection() -> None:
    async def handler1() -> None: ...
    async def handler2() -> None: ...

    e = AsyncEvent(
        handler1,
        handler2,
    )

    assert handler1 in e
    assert handler2 in e

    assert list(e) == [handler1, handler2]

    assert len(e) == 2


def test_Event_add_remove() -> None:
    def handler1() -> None: ...
    def handler2() -> None: ...

    e = Event(handler1)
    assert list(e) == [handler1]

    e += handler2
    assert list(e) == [handler1, handler2]

    e -= handler2
    assert list(e) == [handler1]

    e -= handler2
    assert list(e) == [handler1]

    e += handler2
    e += handler1
    e += handler2
    assert list(e) == [handler1, handler2, handler1, handler2]

    e -= handler1
    assert list(e) == [handler1, handler2, handler2]


def test_AsyncEvent_add_remove() -> None:
    async def handler1() -> None: ...
    async def handler2() -> None: ...

    e = AsyncEvent(handler1)
    assert list(e) == [handler1]

    e += handler2
    assert list(e) == [handler1, handler2]

    e -= handler2
    assert list(e) == [handler1]

    e -= handler2
    assert list(e) == [handler1]

    e += handler2
    e += handler1
    e += handler2
    assert list(e) == [handler1, handler2, handler1, handler2]

    e -= handler1
    assert list(e) == [handler1, handler2, handler2]


def test_Event_invoke() -> None:
    handler1 = Mock()
    handler2 = Mock()

    e = Event(handler1, handler2)
    e(12345, "hello", [True, False], a=0, b=None)

    handler1.assert_called_once_with(12345, "hello", [True, False], a=0, b=None)
    handler2.assert_called_once_with(12345, "hello", [True, False], a=0, b=None)


def test_AsyncEvent_invoke() -> None:
    def as_async(x: Callable):
        async def f(*args, **kwargs):
            return x(*args, **kwargs)
        return f

    handler1 = Mock()
    handler2 = Mock()

    e = AsyncEvent(as_async(handler1), as_async(handler2))
    coroutine = e(12345, "hello", [True, False], a=0, b=None)

    handler1.assert_not_called()
    handler2.assert_not_called()

    asyncio.run(coroutine)

    handler1.assert_called_once_with(12345, "hello", [True, False], a=0, b=None)
    handler2.assert_called_once_with(12345, "hello", [True, False], a=0, b=None)


def test_event() -> None:
    add_mock = Mock()
    remove_mock = Mock()

    class TestClass:
        @event[str]
        def event1():
            return add_mock, remove_mock

    def handler(_: str) -> None: ...

    obj = TestClass()

    add_mock.assert_not_called()
    remove_mock.assert_not_called()

    obj.event1 += handler
    add_mock.assert_called_once_with(obj, handler)

    obj.event1 -= handler
    remove_mock.assert_called_once_with(obj, handler)


def test_async_event() -> None:
    add_mock = Mock()
    remove_mock = Mock()

    class TestClass:
        @async_event[str]
        def event1():
            return add_mock, remove_mock

    async def handler(_: str) -> None: ...

    obj = TestClass()

    add_mock.assert_not_called()
    remove_mock.assert_not_called()

    obj.event1 += handler
    add_mock.assert_called_once_with(obj, handler)

    obj.event1 -= handler
    remove_mock.assert_called_once_with(obj, handler)
