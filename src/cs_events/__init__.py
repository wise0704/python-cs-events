"""
Provides C#-style event handling mechanism.
"""

from ._collections import EventHandlerCollection, EventHandlerDict, EventHandlerList
from ._event import Event, EventHandler, accessors, event
from ._events import events


__all__ = [
    "accessors",
    "event",
    "Event",
    "EventHandler",
    "EventHandlerCollection",
    "EventHandlerDict",
    "EventHandlerList",
    "events",
]
__version__ = "0.2.0"
__author__ = "Daniel Jeong"
