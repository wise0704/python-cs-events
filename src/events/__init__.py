"""
Provides C#-style event handling mechanism.
"""

from ._collections import EventHandlerCollection, EventHandlerDict, EventHandlerList
from ._event import Event, EventHandler, accessors, event
from ._events import event_key, events


__all__ = [
    "accessors",
    "event_key",
    "event",
    "Event",
    "EventHandler",
    "EventHandlerCollection",
    "EventHandlerDict",
    "EventHandlerList",
    "events",
]
__author__ = "Daniel Jeong"
__version__ = "0.4.1"
