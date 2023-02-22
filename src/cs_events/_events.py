import sys
from collections.abc import Callable, Collection, Iterator
from typing import (Any, Final, Literal, ParamSpec, Protocol, TypeVar, final,
                    get_origin, get_type_hints, overload)

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


# Python does not provide a void type, which is a useful feature in callbacks,
# and is clearly different from None.
void = None | Any

P = ParamSpec("P")
EventHandler = Callable[P, void]


@final
class Event(Collection[EventHandler[P]]):
    """
    Represents an event that handlers can subscribe to.

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
        Initializes a new instance of the Event class.

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


class _EmptyEvent(Event[...]):  # type: ignore
    __slots__ = ()

    def __init__(self) -> None:
        pass

    def __iadd__(self, handler: EventHandler[P], /) -> Event[P]:
        return Event(handler)

    def __isub__(self, handler: EventHandler[...], /) -> Self:
        return self

    def __contains__(self, handler: object, /) -> bool:
        return False

    def __iter__(self) -> Iterator[EventHandler[...]]:
        return iter(())

    def __len__(self) -> int:
        return 0

    def __call__(self, *args, **kwargs) -> None:
        pass


_empty_event: Final = _EmptyEvent()


class _Events(Protocol):
    _events: dict[str, Event[...]]


_T = TypeVar("_T", bound=type)
_TEvents = TypeVar("_TEvents", bound=type[_Events])


@overload
def events(cls: _T, /) -> _T: ...


@overload
def events(*, prefix: str = "", properties: Literal[False] = ...) -> Callable[[_T], _T]: ...


@overload
def events(*, prefix: str = "", properties: Literal[True]) -> Callable[[_TEvents], _TEvents]: ...


def events(cls: _T | None = None, /, *, prefix: str = "", properties: bool = False) -> _T | Callable[[_T], _T]:
    """
    Adds event fields/properties based on the annotations defined in the class.

    If this decorator is used to add event fields (`properties=False`), then::

        @events
        class EventFieldsExample:
            on_changed: Event[object, str]
            on_input: Event[int]

    is equivalent to::

        class EventFieldsExample:
            def __init__(self) -> None:
                self.on_changed: Event[object, str] = Event()
                self.on_input: Event[int] = Event()

    Event properties require a dictionary field `_event`::

        @events(properties=True)
        class EventPropertiesExample:
            on_changed: Event[object, str]
            on_input: Event[int]

            def __init__(self) -> None:
                self._events: dict[str, Event[...]] = {}

    If your class defines a large number of events, the storage cost of one field per event might not be acceptable.
    For those situations, event properties can be used to store the events lazily in a dictionary.

    Event properties are slower than event fields due to the additional dictionary structure.
    The trade-off is between memory and speed.
    If your class defines many events that are infrequently raised, you'll want to use event properties.

    Args:
     - cls (type): A class with event annotations.
     - prefix (str, optional): Only process annotations that start with the prefix. Defaults to "".
     - properties (bool, optional): Whether to create event properties instead of fields. Defaults to False.

    Returns:
        (type): cls
    """

    if cls is None:
        if properties:
            return lambda cls: _create_events(cls, prefix)
        return lambda cls: _create_init(cls, prefix)

    if properties:
        return _create_events(cls, prefix)
    return _create_init(cls, prefix)


def _create_init(cls: _T, prefix: str, /) -> _T:
    body_lines: list[str] = []

    for (name, T) in get_type_hints(cls).items():
        if name.startswith(prefix):
            if (get_origin(T) or T) is Event:
                body_lines.append(f"self.{name} = Event()")

    if not body_lines:
        return cls

    globals: dict[str, object] = {"Event": Event}
    locals: dict[str, Callable[..., None]] = {}

    replace = "__init__" in vars(cls)

    if replace:
        globals["__init__"] = cls.__init__
        body_lines.append("__init__(self, *args, **kwargs)")
    else:
        globals["__class__"] = cls
        body_lines.insert(0, "super(__class__, self).__init__(*args, **kwargs)")

    body = "\n".join(f"\t{line}" for line in body_lines)
    exec(f"def __init__(self, *args, **kwargs) -> None:\n{body}", globals, locals)
    func = locals["__init__"]

    if replace:
        for attr in (
            "__module__",
            "__name__",
            "__qualname__",
            "__doc__",
            "__annotations__",
            "__dict__"
        ):
            try:
                value = getattr(cls.__init__, attr)
            except AttributeError:
                pass
            else:
                setattr(func, attr, value)
    else:
        func.__module__ = cls.__module__
        func.__name__ = "__init__"
        func.__qualname__ = f"{cls.__qualname__}.__init__"

    cls.__init__ = func
    return cls


def _create_events(cls: _TEvents, prefix: str, /) -> _TEvents:
    def create_event(name: str, /) -> property:
        def fget(self: _Events, /) -> Event[...]:
            return self._events.get(name, _empty_event)

        def fset(self: _Events, value: Event[...], /) -> None:
            if self._events.setdefault(name, value) is not value:
                raise AttributeError(f"can't set attribute '{name}'", name=name, obj=self)

        def fdel(self: _Events, /) -> None:
            if name in self._events:
                del self._events[name]

        return property(fget, fset, fdel)

    for (name, T) in get_type_hints(cls).items():
        if name.startswith(prefix):
            if (get_origin(T) or T) is Event:
                setattr(cls, name, create_event(name[len(prefix)]))
    return cls
