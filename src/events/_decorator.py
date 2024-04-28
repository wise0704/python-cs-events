import sys
from collections.abc import Callable
from typing import Any, Generic, TypeAlias, TypeVar, overload

from ._common import void


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


__all__ = [
    "accessors",
    "event",
]


TEventHandler = TypeVar("TEventHandler", bound=Callable)


accessors: TypeAlias = tuple[
    Callable[[Any, TEventHandler], void],
    Callable[[Any, TEventHandler], void],
]


class event(Generic[TEventHandler]):
    """
    A decorator used to declare an event property in a publisher class.

    The definition function must return a tuple of accessors `(add, remove)`
    each of type `(Self, TEventHandler) -> void`.

    The subscribe and unsubscribe operators::

        obj.event += handler
        obj.event -= handler

    will invoke the respective `add` and `remove` accessors with the arguments
    `(obj, handler)`.

    An event property is not bound to an instance object, thus it must be accessed as
    an attribute of an object in order for the accessors to be invoked.
    The following code::

        e = obj.event
        e += handler  # no reference to obj!

    has no effect on `obj.event` and will not call the `add` accessor,
    since the argument `self` is not supplied.

    Unlike event fields, an event property cannot be invoked directly.
    Use the underlying event object that the accessors point to instead.

    Example::

        class Example:
            # Infer event handler type from the accessor parameter type
            @event
            def item_added():
                def add(self: Self, value: EventHandler[int, object]) -> None:
                    ...
                def remove(self: Self, value: EventHandler[int, object]) -> None:
                    ...
                return (add, remove)

    Type Args:
        TEventHandler ((...) -> Unknown): Event handler type.
    """

    __slots__ = ["__add", "__remove"]

    @overload
    def __init__(self, definition: Callable[[], accessors[TEventHandler]], /) -> None:
        """
        Initializes a new instance of the `event` class.

        Args:
            definition (() -> accessors[TEventHandler]): An event definition returning a tuple of add and remove accessors.
        """

    @overload
    def __init__(self, accessors: accessors[TEventHandler], /) -> None:
        """
        Initializes a new instance of the `event` class.

        Args:
            accessors (accessors[TEventHandler]): A tuple of add and remove accessors.
        """

    def __init__(self, x: Callable[[], accessors[TEventHandler]] | accessors[TEventHandler], /) -> None:
        (self.__add, self.__remove) = x() if callable(x) else x

    def __get__(self, instance: object, cls: type, /) -> Self:
        return self

    def __set__(self, instance: object, value: tuple[TEventHandler, bool], /) -> None:
        (handler, add) = value
        if add:
            self.__add(instance, handler)
        else:
            self.__remove(instance, handler)

    def __iadd__(self, handler: TEventHandler, /) -> tuple[TEventHandler, bool]:
        """
        Subscribes the handler to this event.

        Args:
            handler (TEventHandler): An event handler.

        Returns:
            tuple[TEventHandler, bool]: The event add operation.
        """

        return (handler, True)

    def __isub__(self, handler: TEventHandler, /) -> tuple[TEventHandler, bool]:
        """
        Unsubscribes the handler from this event.

        Args:
            handler (TEventHandler): An event handler.

        Returns:
            tuple[TEventHandler, bool]: The event remove operation.
        """

        return (handler, False)
