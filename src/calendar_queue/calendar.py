"""A Calendar class, based on CalendarQueue.
It provides helper methods to make the usage of CalendarQueue easier
for dealing with datetime instead of just epoch timestamps.
It also provides an async iterator and a run method for awaiting 
scheduled events and act as they are popped from the queue.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Any, Awaitable, Callable, Generic, Optional

from calendar_queue.calendar_queue import CalendarEvent, CalendarQueue


class Calendar(Generic[CalendarEvent]):
    """An experimental Calendar class to facilitate the use of CalendarQueue
    for scheduling events.

    It can be used as async generator that can be used to await for events.

    Note:
        `CalendarEvent` is a type which represents the objects that
            are scheduled. The type can be a class, a tuple or any sortable
            type, hence it must implement the `__lt__` method.
    """

    def __init__(self) -> None:
        self._calendar_queue: CalendarQueue[CalendarEvent] = CalendarQueue()
        self.executor: Optional[
            Callable[[float | int, CalendarEvent, Calendar], Awaitable[Any]]
            | Callable[[float | int, CalendarEvent, Calendar], Any]
        ] = None
        self._stop_event = asyncio.Event()

    def schedule(self, item: CalendarEvent, when: datetime | float) -> None:
        """Schedule an item. The CalendarEvent object MUST be comparable in
        order to allow ordering of the items in case more than one is
        scheduled for the same timestamp.

        Args:
            item (CalendarEvent): The event to be scheduled
            when (datetime | float): A datetime object or a float representing
                the unix timestamp of the desired scheduled time.
        """

        if isinstance(when, datetime):
            ts = when.timestamp()
        else:
            ts = when

        self._calendar_queue.put_nowait((ts, item))

    def next_scheduled(self) -> Optional[CalendarEvent]:
        """Get the next scheduled event

        Returns:
            Optional[CalendarEvent]: None if nothing is scheduled, otherwise
                the scheduled event.
        """

        return self._calendar_queue.peek()

    def time_remaining(self) -> Optional[float]:
        """Time left until the next scheduled event

        Returns:
            (Optional[float]): Time left in seconds.
        """
        return self._calendar_queue.next_in()

    def cancel_event(
        self, selector: Callable[[tuple[float, CalendarEvent]], bool]
    ) -> list[tuple[float, CalendarEvent]]:
        """Cancel events that match the identifier function.

        Args:
            selector (Callable[[float, CalendarEvent], bool]): A function
                that takes the ts and the event and returns a bool. If it
                returns True, the event will be cancelled.

        Returns:
            (int): number of cancelled events
        """

        return self._calendar_queue.delete_items(selector)

    def events(self) -> list[tuple[float, CalendarEvent]]:
        """Get all scheduled events as a list of tuples."""
        # pylint: disable=protected-access
        return deepcopy(self._calendar_queue._queue)

    def __aiter__(self) -> Calendar[CalendarEvent]:
        """Make the Calendar instance an async iterable.

        Returns:
            Calendar: The Calendar instance itself
        """
        return self

    async def __anext__(self) -> tuple[float, CalendarEvent]:
        """Async iterator method to get the next scheduled event.

        Returns:
            (Tuple(float, CalendarEvent)): A tuple of a timestamp (float)
                and the scheduled event (CalendarEvent)

        Raises:
            StopAsyncIteration: When iteration is stopped via the stop() method
        """

        done, pending = await asyncio.wait(
            [
                asyncio.create_task(
                    self._calendar_queue.get(), name="__calendar_event"
                ),
                asyncio.create_task(
                    self._stop_event.wait(), name="__calendar_stop"
                ),
            ],
            return_when=asyncio.FIRST_COMPLETED,
        )

        event: Optional[tuple[float, CalendarEvent]] = None
        stop = False

        for d in done:
            if e := d.exception():
                raise e

            if "__calendar_event" == d.get_name():
                event = d.result()  # type: ignore
            else:
                stop = True

        for p in pending:
            p.cancel()

        # If the stop event was set AND we got a new event,
        # we honour the stop and put back the gotten event
        # into the queue
        if stop:
            if event is not None:
                self._calendar_queue.put_nowait(event)
            raise StopAsyncIteration

        if event is None:
            raise RuntimeError("Unreachable state reached in Calendar.__anext__")

        return event

    def stop(self) -> None:
        """Stop the execution of the calendar"""

        self._stop_event.set()

    def clear(self) -> list[tuple[float, CalendarEvent]]:
        """Cancel all scheduled events.

        Returns:
            (list[Tuple[float, CalendarEvent]]): The number of cancelled events.
        """

        return self._calendar_queue.delete_items(selector=lambda _: True)
