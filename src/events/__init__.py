"""
Provides C#-style event handling mechanism.
"""

from ._collections import EventHandlerCollection, EventHandlerDict, EventHandlerList
from ._common import Delegate, void
from ._field import AsyncEvent, AsyncEventHandler, Event, EventHandler
from ._property import async_event, event
from ._utils import event_key, events


__all__ = [
    "async_event",
    "AsyncEvent",
    "AsyncEventHandler",
    "Delegate",
    "event_key",
    "event",
    "Event",
    "EventHandler",
    "EventHandlerCollection",
    "EventHandlerDict",
    "EventHandlerList",
    "events",
    "void",
]
__author__ = "Daniel Jeong"
__version__ = "0.4.1"
