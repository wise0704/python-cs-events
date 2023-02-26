from collections.abc import Callable
from typing import TypeVar, get_origin, get_type_hints, overload

from ._event import Event, event


__all__ = [
    "events",
]


_T = TypeVar("_T", bound=type)


@overload
def events(cls: _T, /) -> _T: ...


@overload
def events(*, prefix: str = "", collection: str | None = None) -> Callable[[_T], _T]: ...


def events(cls: _T | None = None, /, *, prefix: str = "", collection: str | None = None) -> _T | Callable[[_T], _T]:
    """
    Adds event fields or properties based on the annotations defined in the class and the specified prefix.

    If this decorator is used to add event fields (``collection=None``),
    then field annotations of type ``Event`` are turned into field assignments in a generated ``__init__`` method.
    The ``__init__`` method will call the original ``__init__`` method at the end of its body if defined,
    or call ``super().__init__`` at the beginning of its body otherwise.

    Example::

        @events(prefix="on_")
        class EventFieldsExample:
            on_change: Event[object, str]
            on_input: Event[int]
            ignored: Event[[]]

    is equivalent to::

        class EventFieldsExample:
            def __init__(self, *args, **kwargs) -> None:
                super().__init__(*args, **kwargs)
                self.on_change: Event[object, str] = Event()
                self.on_input: Event[int] = Event()

    Event properties require ``collection`` to be set to the attribute name of an ``EventHandlerCollection``.
    Field annotations of type ``event`` (NOT ``Event``) are turned into event property definitions,
    using the collection attribute provided and the field name without ``prefix`` as the key.

    Example::

        @events(collection="__events", prefix="on_")
        class EventPropertiesExample:
            on_change: event[object, str]
            on_input: event[int]

            def __init__(self) -> None:
                self.__events = EventHandlerList()

    is equivalent to::

        class EventPropertiesExample:
            @event[object, str]
            def on_change():
                def add(self, value):
                    self.__events.add_handler("change", value)
                def remove(self, value):
                    self.__events.remove_handler("change", value)
                return add, remove

            @event[int]
            def on_input():
                def add(self, value):
                    self.__events.add_handler("input", value)
                def remove(self, value):
                    self.__events.remove_handler("input", value)
                return add, remove

            def __init__(self) -> None:
                self.__events = EventHandlerList()

    If your class defines a large number of events, the storage cost of one field per event might not be acceptable.
    For those situations, event properties can be used to store the events in another data structure.

    Event properties are slower than event fields due to the additional data structure.
    The trade-off is between memory and speed.
    If your class defines many events that are infrequently raised, you'll want to use event properties.

    Args:
     - cls (type): A class with event annotations.
     - prefix (str, optional): Only process annotations that start with the prefix. Defaults to "".
     - collection (str | None, optional): Attribute name of an EventHandlerCollection or None. Defaults to None.

    Returns:
        (type): cls
    """

    if cls is None:
        if collection:  # treat "" as None as well
            return lambda cls: _create_events(cls, prefix, collection)
        return lambda cls: _create_init(cls, prefix)

    if collection:
        return _create_events(cls, prefix, collection)
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
    exec(f"def __init__(self, /, *args, **kwargs) -> None:\n{body}", globals, locals)
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


def _create_events(cls: _T, prefix: str, collection: str, /) -> _T:
    # Assume collection is a valid identifier
    if len(collection) > 2 and collection[:2] == "__" and collection[-2:] != "__":
        collection = f"_{cls.__name__}{collection}"

    locals = {}
    exec(
        "def f(name, /):\n"
        "  def add(self, value, /):\n"
        f"    self.{collection}.add_handler(name, value)\n"

        "  def remove(self, value, /):\n"
        f"    self.{collection}.remove_handler(name, value)\n"

        "  return event(lambda: (add, remove))\n",
        {"event": event},
        locals
    )
    create_event: Callable[[str], event[...]] = locals["f"]

    for (name, T) in get_type_hints(cls).items():
        if name.startswith(prefix):
            if (get_origin(T) or T) is event:
                setattr(cls, name, create_event(name[len(prefix)]))
    return cls
