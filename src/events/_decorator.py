import sys
from collections.abc import Callable
from typing import Any, Generic, Literal, ParamSpec, TypeAlias, overload

from ._common import void
from ._event import AsyncEventHandler, EventHandler


if sys.version_info >= (3, 12):
    from typing import Self, override
else:
    from typing_extensions import Self, override


__all__ = [
    "async_event",
    "event",
]


P = ParamSpec("P")
add: TypeAlias = tuple[EventHandler[P], Literal[True]]
remove: TypeAlias = tuple[EventHandler[P], Literal[False]]


class event(Generic[P]):
    """
    A decorator used to declare an event property in a publisher class.

    The definition function must return a tuple of accessors `(add, remove)`
    each of type `(Self, (**P) -> void) -> void`.

    The subscribe and unsubscribe operators::

        obj.event += handler
        obj.event -= handler

    will invoke the respective `add` and `remove` accessors with the arguments
    `(obj, handler)`.

    An event property is not bound to an instance object, thus it must be
    accessed as an attribute of an object in order for the accessors to be
    invoked. The following code::

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
        **P: Event handler parameter specification.
    """

    __slots__ = ["__add", "__remove"]

    @overload
    def __init__(self, definition: Callable[[], tuple[Callable[[Any, EventHandler[P]], void], Callable[[Any, EventHandler[P]], void]]], /) -> None:
        """
        Initializes a new instance of the `event` class.

        Args:
            definition (() -> tuple[(Self, (**P) -> void) -> void, (Self, (**P) -> void) -> void]):
            An event definition returning a tuple of add and remove accessors.
        """

    @overload
    def __init__(self, accessors: tuple[Callable[[Any, EventHandler[P]], void], Callable[[Any, EventHandler[P]], void]], /) -> None:
        """
        Initializes a new instance of the `event` class.

        Args:
            accessors (tuple[(Self, (**P) -> void) -> void, (Self, (**P) -> void) -> void]): A tuple of add and remove accessors.
        """

    def __init__(
            self,
            x: Callable[[], tuple[Callable[[Any, EventHandler[P]], void], Callable[[Any, EventHandler[P]], void]]]
            | tuple[Callable[[Any, EventHandler[P]], void], Callable[[Any, EventHandler[P]], void]],
            /
    ) -> None:
        (self.__add, self.__remove) = x() if callable(x) else x

    def __get__(self, instance: object, cls: type, /) -> Self:
        return self

    def __set__(self, instance: object, value: add[P] | remove[P], /) -> None:
        (handler, add) = value
        if add:
            self.__add(instance, handler)
        else:
            self.__remove(instance, handler)

    def __iadd__(self, handler: EventHandler[P], /) -> add[P]:
        """
        Subscribes the handler to this event.

        Args:
            handler ((**P) -> void): An event handler.
        """

        return (handler, True)

    def __isub__(self, handler: EventHandler[P], /) -> remove[P]:
        """
        Unsubscribes the handler from this event.

        Args:
            handler ((**P) -> void): An event handler.
        """

        return (handler, False)


class async_event(event[P]):
    """
    A decorator used to declare an asynchronous event property in a publisher
    class.

    The definition function must return a tuple of accessors `(add, remove)`
    each of type `(Self, async (**P) -> void) -> void`.

    The subscribe and unsubscribe operators::

        obj.event += handler
        obj.event -= handler

    will invoke the respective `add` and `remove` accessors with the arguments
    `(obj, handler)`.

    An event property is not bound to an instance object, thus it must be
    accessed as an attribute of an object in order for the accessors to be
    invoked. The following code::

        e = obj.event
        e += handler  # no reference to obj!

    has no effect on `obj.event` and will not call the `add` accessor,
    since the argument `self` is not supplied.

    Unlike event fields, an event property cannot be invoked directly.
    Use the underlying event object that the accessors point to instead.

    Example::

        class Example:
            # Infer event handler type from the accessor parameter type
            @async_event
            def item_added():
                def add(self: Self, value: AsyncEventHandler[int, object]) -> None:
                    ...
                def remove(self: Self, value: AsyncEventHandler[int, object]) -> None:
                    ...
                return (add, remove)

    Type Args:
        **P: Asynchronous event handler parameter specification.
    """

    __slots__ = []

    @overload
    def __init__(self, definition: Callable[[], tuple[Callable[[Any, AsyncEventHandler[P]], void], Callable[[Any, AsyncEventHandler[P]], void]]], /) -> None:
        """
        Initializes a new instance of the `async_event` class.

        Args:
            definition (() -> tuple[(Self, async (**P) -> void) -> void, (Self, async (**P) -> void) -> void]):
            An event definition returning a tuple of add and remove accessors.
        """

    @overload
    def __init__(self, accessors: tuple[Callable[[Any, AsyncEventHandler[P]], void], Callable[[Any, AsyncEventHandler[P]], void]], /) -> None:
        """
        Initializes a new instance of the `async_event` class.

        Args:
            accessors (tuple[(Self, async (**P) -> void) -> void, (Self, async (**P) -> void) -> void]):
            A tuple of add and remove accessors.
        """

    def __init__(self, x, /) -> None:
        super().__init__(x)

    @override
    def __iadd__(self, handler: AsyncEventHandler[P]) -> add[P]:
        """
        Subscribes the handler to this event.

        Args:
            handler (async (**P) -> void): An asynchronous event handler.
        """

        return (handler, True)

    @override
    def __isub__(self, handler: AsyncEventHandler[P]) -> remove[P]:
        """
        Unsubscribes the handler from this event.

        Args:
            handler (async (**P) -> void): An asynchronous event handler.
        """

        return (handler, False)
