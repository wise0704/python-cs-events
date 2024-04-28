import functools
from collections.abc import Callable
from typing import Any, TypeVar, get_origin, get_type_hints, overload

from ._collections import EventHandlerCollection
from ._field import AsyncEvent, Event
from ._property import async_event, event


__all__ = [
    "event_key",
    "events",
]


T = TypeVar("T", bound=type)


@overload
def events(cls: T, /) -> T: ...


@overload
def events(*, collection: str | None = ...) -> Callable[[T], T]: ...


def events(cls: T | None = None, /, *, collection: str | None = None) -> T | Callable[[T], T]:
    """
    Adds event fields and/or properties based on the annotations defined in the
    class.

    ## Event Fields

    Field annotations of type `Event` are turned into field assignments in a
    generated `__init__` method.

    The `__init__` method will execute the original `__init__` method before
    the assignments if defined, or call `super().__init__` otherwise.

    Example::

        @events
        class EventFieldsExample:
            added: Event[object]
            removed: Event[object]

    is equivalent to::

        class EventFieldsExample:
            added: Event[object]
            removed: Event[object]

            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)  # or calls the original __init__(*args, **kwargs)
                self.added = Event()
                self.removed = Event()

    ## Event Properties

    Field annotations of type `event` are turned into event property
    definitions. The add and remove accessors will simply call `add_handler()`
    and `remove_handler()` on the specified collection, with the attribute name
    as the key by default.

    The collection can be specified either by passing the attribute name of an
    `EventHandlerCollection` object as the `collection` argument, or by a field
    annotation of a subtype of `EventHandlerCollection`.

    Example::

        @events(collection="__events")
        class EventPropertiesExample:
            closing: event[CancelEventArgs]
            closed: event[[]]

            def __init__(self) -> None:
                self.__events = EventHandlerList()

    is functionally equivalent to::

        class EventPropertiesExample:
            def __init__(self) -> None:
                self.__events = EventHandlerList()

            @event[CancelEventArgs]
            def closing():
                def add(self, value, /):
                    self.__events.add_handler("closing", value)
                def remove(self, value, /):
                    self.__events.remove_handler("closing", value)
                return (add, remove)

            @event[[]]
            def closed():
                def add(self, value, /):
                    self.__events.add_handler("closed", value)
                def remove(self, value, /):
                    self.__events.remove_handler("closed", value)
                return (add, remove)

    If your class defines a large number of events, the storage cost of one field per event might not be acceptable.
    For those situations, event properties can be used to store the events in another data structure.

    Event properties are slower than event fields due to the additional data structure.
    The trade-off is between memory and speed.
    If your class defines many events that are infrequently raised, you'll want to use event properties.

    Args:
     - cls (type): A class with event annotations.
     - collection (str?, optional): Attribute name of an EventHandlerCollection or None. Defaults to None.

    Returns:
        (type): Returns the same class.
    """

    if cls is None:
        return lambda cls: _events(cls, collection)

    return _events(cls, collection)


def _events(cls: T, collection: str | None, /) -> T:
    if not isinstance(cls, type):
        raise TypeError("Argument 'cls' must be a class.")

    if collection and collection.startswith("__") and not collection.endswith("__"):
        collection = f"_{cls.__name__.lstrip('_')}{collection}"

    fields: list[tuple[str, str]] = []
    properties: list[tuple[str, type[event | async_event]]] = []

    for (attr, T) in get_type_hints(cls).items():
        T = get_origin(T) or T
        if T is Event:
            fields.append((attr, "Event"))
        elif T is AsyncEvent:
            fields.append((attr, "AsyncEvent"))
        elif T is event:
            properties.append((attr, event))
        elif T is async_event:
            properties.append((attr, async_event))
        elif not collection and isinstance(T, type) and issubclass(T, EventHandlerCollection):
            collection = attr

    if fields:
        _fields(cls, fields)

    if properties:
        _properties(cls, properties, collection)

    return cls


def _fields(cls: type, fields: list[tuple[str, str]], /) -> None:
    globals = {
        "__builtins__": {},
        "__orig_init__": cls.__init__,
        "Event": Event,
        "AsyncEvent": AsyncEvent,
    }
    locals: dict[str, Callable] = {}
    exec(
        "def __init__(self, /, *args, **kwargs) -> None:\n "
        "__orig_init__(self, *args, **kwargs)\n " +
        "\n ".join(
            f"self.{attr} = {event_type}()" for (attr, event_type) in fields
        ),
        globals,
        locals
    )

    __init__ = locals["__init__"]

    if "__init__" in cls.__dict__:
        functools.update_wrapper(__init__, cls.__init__)
    else:
        __init__.__module__ = cls.__module__
        __init__.__qualname__ = f"{cls.__qualname__}.__init__"

    cls.__init__ = __init__


def _properties(cls: type, properties: list[tuple[str, type[event | async_event]]], collection: str | None, /) -> None:
    if not collection:
        raise ValueError(
            "Could not find an annotation of type "
            f"'{EventHandlerCollection.__qualname__}' in class '{cls.__qualname__}'."
        )

    # Assume collection is a valid variable name
    locals: dict[str, Callable] = {}
    exec(
        f"def f(key, /):\n"
        f" def add(self, value, /):\n"
        f"  self.{collection}.add_handler(key, value)\n"
        f" def remove(self, value, /):\n"
        f"  self.{collection}.remove_handler(key, value)\n"
        f" return (add, remove)",
        {"__builtins__": {}},
        locals
    )
    f = locals["f"]

    for (name, event_type) in properties:
        setattr(cls, name, event_type(f(getattr(cls, name, name))))


def event_key(key: object, /) -> Any:
    """
    Sets the key to use for event properties created with `@events`.

    Typically, empty objects are used as keys instead of allocating strings.

    Example::

        @events(collection="_events")
        class EventKeyExample:
            __event_added: Final = object()
            __event_removed: Final = object()

            added: event[str] = event_key(__event_added)
            removed: event[str] = event_key(__event_removed)

            def __init__(self) -> None:
                self._events = EventHandlerList()

    Args:
        key (object): A key for the event handler collection to use.

    Returns:
        Any: A hint for the `@events` decorator to use the specified key instead.
    """

    return key
