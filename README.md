# C#-Style Event Handling Mechanism for Python

<p align="center">
    <a href="https://pypi.org/project/cs-events/">
    <img alt="pypi"
    src="https://img.shields.io/pypi/v/cs-events" /></a>
    <a href="https://pypi.org/project/cs-events/">
    <img alt="status"
    src="https://img.shields.io/pypi/status/cs-events" /></a>
    <a href="https://www.python.org/downloads/">
    <img alt="python"
    src="https://img.shields.io/pypi/pyversions/cs-events" /></a>
    <a href="https://github.com/wise0704/python-cs-events/blob/master/LICENSE">
    <img alt="license"
    src="https://img.shields.io/pypi/l/cs-events" /></a>
    <br/>
    <a href="https://github.com/wise0704/python-cs-events/actions/workflows/python-package.yml">
    <img alt="build"
    src="https://img.shields.io/github/actions/workflow/status/wise0704/python-cs-events/python-package.yml" /></a>
    <a href="https://github.com/wise0704/python-cs-events/issues">
    <img alt="issues"
    src="https://img.shields.io/github/issues/wise0704/python-cs-events" /></a>
    <a href="https://github.com/wise0704/python-cs-events/pulls">
    <img alt="pull requests"
    src="https://img.shields.io/github/issues-pr-closed/wise0704/python-cs-events" /></a>
</p>

C# provides a very simple syntax using the [observer pattern](https://en.wikipedia.org/wiki/Observer_pattern) for its event handling system.
The aim of this project is to implement the pattern in python as similarly as possible.

In C#, an "event" is a field or a property of the delegate type `EventHandler`.
Since delegates in C# can be combined and removed with `+=` and `-=` operators,
event handlers can easily subscribe to or unsubscribe from the event using those operators.

Python does not support an addition of two `Callable` types.
So the `Event[P]` class is provided to mimic delegates:

```python
from cs_events import Event

on_change = Event[object, str]()
```

Handlers can subscribe to and unsubscribe from the event with the same syntax:

```python
def event_handler(o: object, s: str) -> None: ...

on_change += event_handler
on_change -= event_handler
```

An event can be raised by simply invoking it with the arguments:

```python
on_change(obj, "value")
```

Since `Event` acts just like a delegate from C#, it is not required to be bound to a class or an instance object.
This is the major difference to other packages that try to implement the C#-style event system, which usually revolve around a container object for events.

An example class with event fields may look like this:

```python
class EventExample:
    def __init__(self) -> None:
        self.on_update: Event[str] = Event()
        self.__value: str = ""

    def update(self, value: str) -> None:
        if self.__value != value:
            self.__value = value
            self.on_update(value)

obj = EventExample()
obj.on_update += lambda value: print(f"obj.{value=}")
obj.update("new value")
```

A class decorator `@events` is provided as a shortcut for event fields:

```python
from cs_events import Event, events

@events
class EventFieldsExample:
    item_added: Event[object]
    item_removed: Event[object]
    item_updated: Event[object, str]
```

C# also provides event properties with `add` and `remove` accessors:

```C#
public event EventHandler<T> Changed
{
    add => ...
    remove => ...
}
```

This feature is useful for classes that do not actually own the events, but need to forward the subscriptions to the underlying object that do own the events.

The `@event[P]` decorator and the `accessors[P]` type are provided to support this feature:

```python
from cs_events import accessors, event, EventHandler

class EventPropertyExample:
    @event[str, object]
    def on_change() -> accessors[str, object]:
        def add(self: Self, value: EventHandler[str, object]) -> None:
            ...
        def remove(self: Self, value: EventHandler[str, object]) -> None:
            ...
        return add, remove
```

Furthermore, the `EventHandlerCollection` interface is provided to support the functionalities of `System.ComponentModel.EventHandlerList` class from C#, along with the two implementations `EventHandlerList` and `EventHandlerDict` using a linked list and a dictionary respectively. The behaviour of `EventHandlerList` is exactly the same as of its counterpart from C#.

A typical usage of `EventHandlerList` in C# can be translated directly into the python code:

```python
class EventPropertyExample:
    __event_change: Final = object()

    @event  # [str, object] is inferred
    def on_change():  # -> accessors[str, object] is inferred
        def add(self: Self, value: EventHandler[str, object]) -> None:
            self.__events.add_handler(self.__event_change, value)
        def remove(self: Self, value: EventHandler[str, object]) -> None:
            self.__events.remove_handler(self.__event_change, value)
        return add, remove
    
    def __init__(self) -> None:
        self.__events = EventHandlerList()
    
    def perform_change(key: str, value: object) -> None:
        e = self.__events[self.__event_change]
        if e is not None:
            e(key, value)
```

The class decorator `@events` also provides a shortcut for event properties.
The above code can be shortened to:

```python
@events(collection="__events", prefix="on_")
class EventPropertyExample:
    on_change: event[object, str]

    def __init__(self) -> None:
        self.__events = EventHandlerList()

    def perform_change(key: str, value: object) -> None:
        self.__events.invoke("change", key, value)
```

## Installation

Install using [`pip`](https://pypi.org/project/pip/):

```console
pip install cs-events
```
