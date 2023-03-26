from unittest.mock import Mock
import pytest

from events import Event, EventHandlerCollection, EventHandlerDict, EventHandlerList


@pytest.mark.parametrize("collection", [EventHandlerList(), EventHandlerDict()])
def test_EventHandleCollection(collection: EventHandlerCollection) -> None:
    collection = EventHandlerList()
    key1 = object()
    key2 = object()

    def delegate(): ...

    assert collection[key1] is None
    assert collection[key2] is None

    collection.remove_handler(key1, delegate)

    assert collection[key1] is None
    assert collection[key2] is None

    collection.remove_handler(key2, delegate)

    assert collection[key1] is None
    assert collection[key2] is None

    collection.add_handler(key1, delegate)

    assert isinstance(e := collection[key1], Event)
    assert len(e) == 1
    assert collection[key2] is None

    collection.add_handler(key1, delegate)

    assert isinstance(e := collection[key1], Event)
    assert len(e) == 2
    assert collection[key2] is None

    collection.add_handler(key2, delegate)

    assert isinstance(e := collection[key1], Event)
    assert len(e) == 2
    assert isinstance(e := collection[key2], Event)
    assert len(e) == 1

    mock1 = Mock()
    mock2 = Mock()

    collection.add_handler(key1, mock1)
    collection.add_handler(key1, mock2)
    collection.add_handler(key1, mock1)

    assert (e := collection[key1])
    assert list(e) == [delegate, delegate, mock1, mock2, mock1]

    collection.remove_handler(key1, delegate)
    collection.remove_handler(key1, delegate)
    collection.remove_handler(key1, mock1)

    assert list(e) == [mock1, mock2]

    collection.invoke(key1, "TEST")
    mock1.assert_called_once_with("TEST")
    mock2.assert_called_once_with("TEST")
