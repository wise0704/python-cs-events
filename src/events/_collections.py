from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, Union, runtime_checkable

from ._event import Event


__all__ = [
    "EventHandlerCollection",
    "EventHandlerList",
    "EventHandlerDict",
]


void = object


@runtime_checkable
class EventHandlerCollection(Protocol):
    """
    Provides a collection of event handler delegates.
    """

    __slots__ = ()

    def __getitem__(self, key: object, /) -> Event[...] | None:
        """
        Gets the event for the specified key.

        Args:
         - key (object): A key to find in the list.

        Returns:
            (Event[...]?): The event for the specified key, or ``None`` if an event does not exist.
        """

        ...

    def add_handler(self, key: object, value: Callable[..., void], /) -> None:
        """
        Adds the delegate to the list.

        Args:
         - key (object): A key that owns the event.
         - value ((...) -> void): A delegate to add to the list.
        """

        ...

    def remove_handler(self, key: object, value: Callable[..., void], /) -> None:
        """
        Removes the delegate from the list.

        Args:
         - key (object): A key that owns the event.
         - value ((...) -> void): A delegate to remove from the list.
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


if TYPE_CHECKING:
    ListEntry = tuple[object, Event[...], Union["ListEntry", None]]


class EventHandlerList(EventHandlerCollection):
    """
    Provides a simple linked list of event handler delegates.
    """

    __slots__ = ("__head")

    def __init__(self) -> None:
        """
        Initializes a new instance of the ``EventHandlerList`` class.
        """

        self.__head: ListEntry | None = None

    def __getitem__(self, key: object, /) -> Event[...] | None:
        next = self.__head
        while next is not None:
            (k, e, next) = next
            if k == key:  # use __eq__ instead of "is"
                return e
        return None

    def add_handler(self, key: object, value: Callable[..., void], /) -> None:
        if (e := self[key]) is None:
            self.__head = (key, Event(value), self.__head)
        else:
            e += value


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

    def add_handler(self, key: object, value: Callable[..., void], /) -> None:
        if (e := self[key]) is None:
            self.__dict[key] = Event(value)
        else:
            e += value
