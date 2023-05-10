"""
Provides thread-safe classes for event handling.
"""

import sys
from threading import Lock
from typing import TYPE_CHECKING, ParamSpec, Union

from ._collections import EventHandlerCollection
from ._event import Event, EventHandler


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


__all__ = [
    "ConcurrentEventHandlerList",
]


P = ParamSpec("P")


class VolatileEvent(Event[P]):
    __slots__ = ("__lock")

    def __init__(self, *handlers: EventHandler[P]) -> None:
        super().__init__(*handlers)
        self.__lock = Lock()

    def __iadd__(self, value: EventHandler[P], /) -> Self:
        self.__lock.acquire()
        super().__iadd__(value)
        self.__lock.release()
        return self

    def __isub__(self, value: EventHandler[P], /) -> Self:
        self.__lock.acquire()
        super().__isub__(value)
        self.__lock.release()
        return self

    def __contains__(self, obj: object, /) -> bool:
        self.__lock.acquire()
        x = super().__contains__(obj)
        self.__lock.release()
        return x

    def __len__(self) -> int:
        self.__lock.acquire()
        x = super().__len__()
        self.__lock.release()
        return x

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        self.__lock.acquire()
        handlers = [*self]
        self.__lock.release()
        for handler in handlers:
            handler(*args, **kwargs)


if TYPE_CHECKING:
    ListEntry = tuple[object, VolatileEvent[...], Union["ListEntry", None]]


class ConcurrentEventHandlerList(EventHandlerCollection):
    """
    Provides a simple thread-safe linked list of event handler delegates.
    """

    __slots__ = ("__head", "__lock")

    def __init__(self) -> None:
        """
        Initializes a new instance of the ``ConcurrentEventHandlerList`` class.
        """

        self.__head: ListEntry | None = None
        self.__lock = Lock()

    def __getitem__(self, key: object, /) -> Event[...] | None:
        # self.__lock.acquire()
        next = self.__head  # Assignment should be atomic regardless of GIL
        # self.__lock.release()
        while next is not None:
            (k, e, next) = next
            if k == key:
                return e
        return None

    def add_handler(self, key: object, value: EventHandler[...], /) -> None:
        self.__lock.acquire()
        if (e := self[key]) is None:
            self.__head = (key, VolatileEvent(value), self.__head)
            self.__lock.release()
        else:
            self.__lock.release()
            e += value


class ConcurrentEventHandlerDict(EventHandlerCollection):
    """
    Provides a simple thread-safe dictionary of event handler delegates.
    """

    __slots__ = ("__dict", "__lock")

    def __init__(self) -> None:
        """
        Initializes a new instance of the ``ConcurrentEventHandlerDict`` class.
        """

        self.__dict: dict[object, VolatileEvent[...]] = {}
        self.__lock = Lock()

    def __getitem__(self, key: object, /) -> Event[...] | None:
        self.__lock.acquire()
        x = self.__dict.get(key)
        self.__lock.release()
        return x

    def add_handler(self, key: object, value: EventHandler[...], /) -> None:
        self.__lock.acquire()
        if (e := self.__dict.get(key)) is None:
            self.__dict[key] = VolatileEvent(value)
            self.__lock.release()
        else:
            self.__lock.release()
            e += value
