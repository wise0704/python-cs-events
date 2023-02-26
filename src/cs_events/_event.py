import sys
from collections.abc import Callable, Collection, Iterator
from typing import Any, Generic, ParamSpec, final


if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


__all__ = [
    "accessors",
    "event",
    "Event",
    "EventHandler",
]

# Python does not provide a void type, which is a useful feature in callbacks,
# and is clearly different from None.
# Comparison with TS:
#     function foo(): void {} <==> def foo() -> None: pass
#     let bar: () => void;    <==> bar: Callable[[], Any]
void = None | Any

P = ParamSpec("P")
EventHandler = Callable[P, void]
accessors = tuple[Callable[[Any, EventHandler[P]], void], Callable[[Any, EventHandler[P]], void]]


@final
class Event(Collection[EventHandler[P]]):
    """
    Represents an event delegate that handlers can subscribe to.

    The type argument specifies the event data parameters::

        event = Event[str, int]()
        # accepts handlers (str, int) -> void

    Handlers can subscribe to and unsubscribe from an event by::

        event += event_handler
        event -= event_handler

    An event can be raised by invoking itself with the necessary arguments::

        event(...)

    Type Args:
     - P (ParamSpec): Event data parameter specification.
    """

    __slots__ = ("__handlers")

    __handlers: list[EventHandler[P]]

    def __init__(self, *handlers: EventHandler[P]) -> None:
        """
        Initializes a new instance of the ``Event`` class.

        Args:
         - *handlers ((**P) -> void): List of handlers to subscribe to the event.
        """

        self.__handlers = [*handlers]

    def __iadd__(self, handler: EventHandler[P], /) -> Self:
        """
        Subscribes the handler to this event.

        Args:
         - handler ((**P) -> void): An event handler.

        Returns:
            (Self): This event.
        """

        self.__handlers.append(handler)
        return self

    def __isub__(self, handler: EventHandler[P], /) -> Self:
        """
        Unsubscribes the handler from this event.

        If the handler has been added multiple times, removes only the last occurrence.

        Args:
         - handler ((**P) -> void): An event handler

        Returns:
            (Self): This event
        """

        for i in reversed(range(len(self.__handlers))):
            if self.__handlers[i] is handler:
                del self.__handlers[i]
                break
        return self

    def __contains__(self, handler: object, /) -> bool:
        """
        Returns whether the handler has been subscribed to this event.

        Args:
         - handler (object): An event handler.

        Returns:
            (bool): True if handler is subscribed, False otherwise.
        """

        return self.__handlers.__contains__(handler)

    def __iter__(self) -> Iterator[EventHandler[P]]:
        """
        Returns an iterator from the list of subscribed handlers.

        Yields:
            ((**P) -> void): A subscribed event handler.
        """

        return self.__handlers.__iter__()

    def __len__(self) -> int:
        """
        Returns the number of subscribed handlers.

        Returns:
            (int): The number of subscribed event handlers.
        """

        return self.__handlers.__len__()

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Raises this event.

        Handlers will be invoked in the order they subscribed.
        """

        for handler in [*self.__handlers]:  # apparently faster than list.copy(), list[:] or even (*list, )
            handler(*args, **kwargs)


@final
class event(Generic[P]):
    """
    A decorator used to declare an event property in a publisher class.

    The definition function must return a tuple of accessors ``(add, remove)``
    each of type ``(Self, (**P) -> void) -> void``.

    The subscribe and unsubscribe operators::

        obj.event += handler
        obj.event -= handler

    will invoke the respective `add` and `remove` accessors with the arguments
    `(obj, handler)`.

    An event property is not bound to an instance object, thus it must be accessed as
    an attribute of an object in order for the accessors to be invoked.
    The following code::

        e = obj.event
        e += handler  # no effect on obj.event

    has no effect on `obj.event` and will not call the `add` accessor,
    since the argument `self` cannot be supplied.

    Unlike event fields, an event property cannot be invoked directly.
    Use the underlying event that the accessors point to instead.

    Example::

        class Example:
            # Infer event type from the accessor parameter type
            @event
            def item_added():
                def add(self: Self, value: EventHandler[int, object]):
                    ...
                def remove(self: Self, value: EventHandler[int, object]):
                    ...
                return add, remove

            # Infer event type from the accessors type
            @event
            def item_removed() -> accessors[int, object]:
                def add(self: Self, value):
                    ...
                def remove(self: Self, value):
                    ...
                return add, remove

            # Explicit event type
            @event[int, object]
            def item_changed():
                def add(self: Self, value):
                    ...
                def remove(self: Self, value):
                    ...
                return add, remove
    """

    __slots__ = ("__add", "__remove")

    def __init__(self, f: Callable[[], accessors[P]], /) -> None:
        """
        Initializes a new instance of the ``event`` class.

        Args:
            f (() -> accessors[P]): An event definition.
        """
        (self.__add, self.__remove) = f()

    def __get__(self, instance: object, cls: type, /) -> Self:
        return self

    def __set__(self, instance: object, value: tuple[EventHandler[P], bool], /) -> None:
        (handler, add) = value
        if add:
            self.__add(instance, handler)
        else:
            self.__remove(instance, handler)

    def __iadd__(self, handler: EventHandler[P], /) -> tuple[EventHandler[P], bool]:
        return (handler, True)

    def __isub__(self, handler: EventHandler[P], /) -> tuple[EventHandler[P], bool]:
        return (handler, False)
