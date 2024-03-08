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
from typing import Any, AsyncGenerator, Awaitable, Callable, Generic, Optional

from calendar_queue.calendar_queue import CalendarEvent, CalendarQueue
from calendar_queue.exceptions import CalendarMissingExecutor


class Calendar(Generic[CalendarEvent]):
    """An experimental Calendar class to facilitate the use of CalendarQueue
    for scheduling events.

    It provides a an `events` method which returns an async generator that
    can be used to await for events.

    Additionally it provides a `run` method which can be used only after
    setting an executor function, the executor can be an a sync or an async
    function and will be called every time an event is scheduled to happen,
    receiving the scheduled timestamp, the event and the Calendar object.


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

    def set_executor(
        self,
        executor: (
            Callable[[float | int, CalendarEvent, Calendar], Awaitable[Any]]
            | Callable[[float | int, CalendarEvent, Calendar], Any]
        ),
    ) -> None:
        """This method can be used to set an executor function which will
        used in the `run` method every time an event is scheduled to happen.

        Args:
            executor (CalendarExecutor): A sync or async function which takes as
                argument the scheduled timestamp of the event and the event.
        """

        self.executor = executor

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

    def remaining_events(self) -> list[tuple[float, CalendarEvent]]:
        """Return the remaining scheduled events

        Returns:
            (int): The number of scheduled events
        """

        # pylint: disable=protected-access
        return deepcopy(self._calendar_queue._queue)

    async def events(self) -> AsyncGenerator[tuple[float, CalendarEvent], None]:
        """This method returns an async generator which can be used for
        awaiting events.

        Yields:
            (Tuple(float, CalendarEvent)): A tuple of a timestamp (float)
                and the scheduled event (CalendarEvent)
        """
        self._stop_event.clear()

        while True:

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
                return

            yield event

    async def run(self) -> None:
        """This method requires an executor to be set with `set_executor`.
        It will internally await for events and call the executor every
        time an event is scheduled to happen


        Raises:
            CalendarMissingExecutor: If the executor is not set.
        """

        if self.executor is None:
            raise CalendarMissingExecutor(
                "Executor function must be set to run the calendar"
            )

        self._stop_event.clear()

        async for ts, event in self.events():

            if asyncio.iscoroutinefunction(self.executor):
                await self.executor(ts, event, self)
            else:
                self.executor(ts, event, self)

    def stop(self) -> None:
        """Stop the execution of the calendar"""

        self._stop_event.set()

    def clear(self) -> list[tuple[float, CalendarEvent]]:
        """Cancel all scheduled events.

        Returns:
            (list[Tuple[float, CalendarEvent]]): The number of cancelled events.
        """

        return self._calendar_queue.delete_items(selector=lambda _: True)


# Define Executor type hint, for users only
CalendarExecutor = (
    Callable[[float | int, CalendarEvent, Calendar], Awaitable[Any]]
    | Callable[[float | int, CalendarEvent, Calendar], Any]
)
