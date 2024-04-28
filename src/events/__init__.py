"""
Provides C#-style event handling mechanism.
"""

from ._collections import EventHandlerCollection, EventHandlerDict, EventHandlerList
from ._common import Delegate, void
from ._decorator import accessors, event
from ._event import AsyncEvent, AsyncEventHandler, Event, EventHandler


__all__ = [
    "accessors",
    "AsyncEvent",
    "AsyncEventHandler",
    "Delegate",
    "event",
    "Event",
    "EventHandler",
    "EventHandlerCollection",
    "EventHandlerDict",
    "EventHandlerList",
    "void",
]
__author__ = "Daniel Jeong"
__version__ = "0.4.1"
