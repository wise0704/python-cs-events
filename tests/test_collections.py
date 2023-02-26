import pytest

from cs_events import Event, EventHandlerCollection, EventHandlerDict, EventHandlerList


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
