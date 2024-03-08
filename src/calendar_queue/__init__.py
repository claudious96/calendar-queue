"""A package implementing an asyncio based calendar queue and a calendar """

from .calendar_queue import CalendarEvent, CalendarQueue
from .calendar import Calendar
from .exceptions import CalendarMissingExecutor

__version__ = "0.1.0"
