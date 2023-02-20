import sys
from collections.abc import Callable, Collection, Iterator
from typing import Any, ClassVar, Final, ParamSpec, get_origin, get_type_hints

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


# Python does not provide a void type, which is a useful feature in callbacks,
# and is clearly different from None.
void = None | Any

P = ParamSpec("P")
EventHandler = Callable[P, void]


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


class _EmptyEvent(Event[...]):
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


class EventDispatcher:
    """
    A base class that provides basic functionality to support dictionary-based event properties.

    Event fields::

        class EventFieldsExample:
            def __init__(self) -> None:
                self.on_changed = Event[object, str]()
                self.on_input = Event[int]()
                ...

    Event properties::

        class EventPropertiesExample(EventDispatcher):
            on_changed: Event[object, str]
            on_input: Event[int]

            def __init__(self) -> None:
                super().__init__()
                ...

    If your class defines a large number of events, the storage cost of one field per event might not be acceptable.
    For those situations, EventDispatcher provides event properties that stores the events lazily in a dictionary.

    Event properties are slower than event fields due to the additional dictionary structure.
    The trade-off is between memory and speed.
    If your class defines many events that are infrequently raised, or only few of the events are handled,
    you'll want to use event properties.
    """

    default_prefix: ClassVar[str] = ""
    """
    (static str) The default prefix to use when `None` is passed to `event_prefix`.
    """

    __slots__ = ("__events")

    __events: dict[str, Event[...]]

    def __init__(self, *args, **kwargs) -> None:
        """
        Initializes a new instance of the EventDispatcher class.

        This must be called in order for event properties to work.
        """

        super().__init__(*args, **kwargs)
        self.__events = {}

    def __init_subclass__(cls, *, event_prefix: str | None = None, del_empty_event: bool = False, **kwargs) -> None:
        """
        This method is called when this class is subclassed.

        This must be called in order for event properties to work.

        Args:
         - event_prefix (str | None, optional):
            When specified, only annotations that start with the prefix are processed.
            If unspecified or None, then the value `EventDispatcher.default_prefix` is used.
            Defaults to None.  
         - del_empty_event (bool, optional): 
            Whether to automatically delete an event from the dictionary if it's set to an empty event.
            Defaults to False.
        """

        super().__init_subclass__(**kwargs)

        if event_prefix is None:
            event_prefix = cls.default_prefix

        def create_event(name: str, T: type[Event[...]], is_subclass: bool, /) -> property:
            if is_subclass:
                def fget(self: EventDispatcher, /) -> T:
                    if (event := self.__events.get(name)) is None:
                        event = self.__events[name] = T()
                    return event

            else:
                def fget(self: EventDispatcher, /) -> T:
                    return self.__events.get(name, _empty_event)

            if del_empty_event:
                def fset(self: EventDispatcher, value: T, /) -> None:
                    if len(value):
                        self.__events[name] = value
                    elif name in self.__events:
                        del self.__events[name]
            else:
                def fset(self: EventDispatcher, value: T, /) -> None:
                    self.__events[name] = value

            def fdel(self: EventDispatcher, /) -> None:
                if name in self.__events:
                    del self.__events[name]

            return property(fget, fset, fdel)

        for (name, T) in get_type_hints(cls).items():
            if name.startswith(event_prefix):
                T = get_origin(T) or T
                if isinstance(T, type) and issubclass(T, Event):
                    setattr(cls, name, create_event(name[len(event_prefix):], T, T is not Event))


class EventFields:
    default_prefix: str = ""
    """
    (static str) The default prefix to use when `None` is passed to `event_prefix`.
    """

    __slots__ = ("__events__")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        for (name, T) in self.__events__:
            setattr(self, name, T())

    def __init_subclass__(cls, *, event_prefix: str | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        if event_prefix is None:
            event_prefix = cls.default_prefix

        cls.__events__: list[tuple[str, type[Event[...]]]] = [
            (name, T)
            for (name, T) in get_type_hints(cls).items()
            if name.startswith(event_prefix)
            if issubclass(get_origin(T) or T, Event)
        ]
