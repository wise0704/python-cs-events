import asyncio
import sys
from collections.abc import Callable, Coroutine
from typing import Any, ParamSpec, TypeAlias

from ._common import Delegate, void


if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override


__all__ = [
    "AsyncEvent",
    "AsyncEventHandler",
    "Event",
    "EventHandler",
]


P = ParamSpec("P")


EventHandler: TypeAlias = Callable[P, void]
"""
Represents the method that will handle an event.
"""

AsyncEventHandler: TypeAlias = Callable[P, Coroutine[void, void, void]]
"""
Represents the method that will handle an event asynchronously.
"""


class Event(Delegate[P, void]):
    """
    Represents an event delegate that handlers can subscribe to.

    The type argument specifies the event handler parameters::

        changed = Event[str, int]()
        # accepts handlers: (str, int) -> void

    Handlers can subscribe to and unsubscribe from an event by::

        changed += changed_handler
        changed -= changed_handler

    An event can be raised by invoking itself with the necessary arguments::

        changed("key", 0)

    Type Args:
        **P: Event handler parameter specification.
    """

    __slots__ = []

    @override
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Raises this event.

        Handlers will be invoked in the order they subscribed.
        """

        for handler in self.get_invocation_list():
            handler(*args, **kwargs)


class AsyncEvent(Delegate[P, Coroutine[Any, Any, void]]):
    """
    Represents an asynchronous event delegate that handlers can subscribe to.

    The type argument specifies the event handler parameters::

        changed = AsyncEvent[str, int]()
        # accepts handlers: async (str, int) -> void

    Handlers can subscribe to and unsubscribe from an asynchronous event by::

        changed += changed_handler
        changed -= changed_handler

    An asynchronous event can be raised by invoking itself with the
    necessary arguments and executing the coroutine::

        await changed("key", 0)

    Args:
        **P: Asynchronous event handler parameter specification.
    """

    __slots__ = []

    if sys.version_info >= (3, 11):
        @override
        async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
            """
            Asynchronously raises this event using `asyncio.TaskGroup`.

            Handlers will be invoked in the order they subscribed.
            """

            async with asyncio.TaskGroup() as tg:
                for handler in self.get_invocation_list():
                    tg.create_task(handler(*args, **kwargs))
    else:
        @override
        async def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
            """
            Asynchronously raises this event using `asyncio.gather()`.

            Handlers will be invoked in the order they subscribed.
            """

            coroutines = [handler(*args, **kwargs) for handler in self.get_invocation_list()]
            await asyncio.gather(*coroutines, return_exceptions=False)
