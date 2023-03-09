from collections.abc import Callable
from typing import Any, Protocol, Union, runtime_checkable

from ._event import Event


__all__ = [
    "EventHandlerCollection",
    "EventHandlerList",
    "EventHandlerDict",
]


@runtime_checkable
class EventHandlerCollection(Protocol):
    """
    Provides a collection of event handler delegates.
    """

    def __getitem__(self, key: object, /) -> Event[...] | None:
        """
        Gets the event for the specified key.

        Args:
         - key (object): A key to find in the list.

        Returns:
            (Event[...]?): The event for the specified key, or ``None`` if an event does not exist.
        """

        ...

    def add_handler(self, key: object, value: Callable[..., Any], /) -> None:
        """
        Adds the delegate to the list.

        Args:
         - key (object): A key that owns the event.
         - value ((...) -> Any): A delegate to add to the list.
        """

        ...

    def remove_handler(self, key: object, value: Callable[..., Any], /) -> None:
        """
        Removes the delegate from the list.

        Args:
         - key (object): A key that owns the event.
         - value ((...) -> Any): A delegate to remove from the list.
        """

        if (e := self[key]) is not None:
            e -= value

    def invoke(self, key: object, /, *args, **kwargs) -> None:
        """
        Invokes an event from the list.

        Equivalent to::

            e = events[key]
            if e is not None:
                e(...)

        This method is provided as a shortcut to above,
        since python does not have null-conditional operators::

            events[key]?.__call__(...)  # C# style func?.Invoke(...)
            events[key]?.(...)  # JavaScript style func?.(...)

        Args:
         - key (object): A key that owns the event.
        """

        if (e := self[key]) is not None:
            e(*args, **kwargs)


_ListEntry = tuple[object, Event[...], Union["_ListEntry", None]]


class EventHandlerList(EventHandlerCollection):
    """
    Provides a simple linked list of event handler delegates.
    """

    __slots__ = ("__head")

    def __init__(self) -> None:
        """
        Initializes a new instance of the ``EventHandlerList`` class.
        """

        self.__head: _ListEntry | None = None

    def __getitem__(self, key: object, /) -> Event[...] | None:
        next = self.__head
        while next is not None:
            _key, handler, next = next
            if _key == key:  # use __eq__ instead of "is"
                return handler
        return None

    def add_handler(self, key: object, value: Callable[..., Any], /) -> None:
        if (e := self[key]) is not None:
            e += value
        else:
            self.__head = (key, Event(value), self.__head)


class EventHandlerDict(EventHandlerCollection):
    """
    Provides a simple dictionary of event handler delegates.
    """

    __slots__ = ("__dict")

    def __init__(self) -> None:
        """
        Initializes a new instance of the ``EventHandlerDict`` class.
        """

        self.__dict: dict[object, Event[...]] = {}

    def __getitem__(self, key: object, /) -> Event[...] | None:
        return self.__dict.get(key)

    def add_handler(self, key: object, value: Callable[..., Any], /) -> None:
        if (e := self[key]) is not None:
            e += value
        else:
            self.__dict[key] = Event(value)
