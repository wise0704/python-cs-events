import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING, Union

from ._common import Delegate
from ._field import Event


if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


__all__ = [
    "EventHandlerCollection",
    "EventHandlerList",
    "EventHandlerDict",
]


class EventHandlerCollection(ABC):
    """
    Provides a collection of event handler delegates.
    """

    __slots__ = []

    @abstractmethod
    def __getitem__(self, key: object, /) -> Delegate | None:
        """
        Gets the event for the specified key.

        Args:
            key (object): A key to find in the collection.

        Returns:
            Delegate | None: The event for the specified key, or `None` if an event does not exist.
        """

        raise NotImplementedError

    @abstractmethod
    def add_handler(self, key: object, value: Callable, event_type: type[Delegate] = Event, /) -> None:
        """
        Adds the delegate to the collection.

        Args:
            key(object): A key that owns the event.
            value((...) -> Unknown): A delegate to add to the collection.
            event_type (type[Delegate], optional): The type of the event. Defaults to `Event`.
        """

        raise NotImplementedError

    def remove_handler(self, key: object, value: Callable, /) -> None:
        """
        Removes the delegate from the collection.

        Args:
         - key (object): A key that owns the event.
         - value ((...) -> Unknown): A delegate to remove from the collection.
        """

        if (e := self[key]) is not None:
            e -= value

    def invoke(self, key: object, /, *args, **kwargs) -> None:
        """
        Invokes an event from the collection.

        Equivalent to::

            e = events[key]
            if e is not None:
                e(...)

        This method is provided as a shortcut to above,
        since python does not have null-conditional operators::

            events[key]?.__call__(...)  # C# style func?.Invoke(...)
            events[key]?.(...)          # JS/TS style func?.(...)

        Args:
            key (object): A key that owns the event.
        """

        if (e := self[key]) is not None:
            e(*args, **kwargs)

    async def invoke_async(self, key: object, /, *args, **kwargs) -> None:
        """
        Asynchronously invokes an event from the collection.

        Equivalent to::

            e = events[key]
            if e is not None:
                await e(...)

        Args:
            key (object): A key that owns the event.
        """

        if (e := self[key]) is not None:
            await e(*args, **kwargs)


if TYPE_CHECKING:
    ListEntry = tuple[object, Delegate, Union["ListEntry", None]]


class EventHandlerList(EventHandlerCollection):
    """
    Provides a simple linked list of event handler delegates.
    """

    __slots__ = ["__head"]

    def __init__(self) -> None:
        """
        Initializes a new instance of the `EventHandlerList` class.
        """

        self.__head: ListEntry | None = None

    @override
    def __getitem__(self, key: object, /) -> Delegate | None:
        next = self.__head
        while next is not None:
            (k, e, next) = next
            if k == key:
                return e
        return None

    @override
    def add_handler(self, key: object, value: Callable, event_type: type[Delegate] = Event, /) -> None:
        if (e := self[key]) is None:
            self.__head = (key, event_type(value), self.__head)
        else:
            e += value


class EventHandlerDict(EventHandlerCollection):
    """
    Provides a simple dictionary of event handler delegates.
    """

    __slots__ = ["__dict"]

    def __init__(self) -> None:
        """
        Initializes a new instance of the `EventHandlerDict` class.
        """

        self.__dict: dict[object, Delegate] = {}

    @override
    def __getitem__(self, key: object, /) -> Delegate | None:
        return self.__dict.get(key)

    @override
    def add_handler(self, key: object, value: Callable, event_type: type[Delegate] = Event, /) -> None:
        if (e := self[key]) is None:
            self.__dict[key] = event_type(value)
        else:
            e += value
