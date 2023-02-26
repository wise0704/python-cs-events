from unittest.mock import Mock

from cs_events import Event, event


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
