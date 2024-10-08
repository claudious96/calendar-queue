"""A CalendarQueue class, based on asyncio's priority queue.
It accepts items as long as they are sortable and provides
async method for putting and getting items from the queue
as well as checking what is currently in the queue and 
delete existing elements. 
"""

from asyncio import Queue, QueueFull, TimerHandle
from heapq import heappop as heap_pop
from heapq import heappush as heap_push
import math
import sys
from time import time
from typing import Callable, Generic, Optional, TypeVar, Union

if sys.version_info >= (3, 13):
    from asyncio import QueueShutDown
else:
    QueueShutDown = ValueError


CalendarEvent = TypeVar("CalendarEvent")


class CalendarQueue(Queue, Generic[CalendarEvent]):
    """A subclass of Queue; retrieves entries in priority order (lowest first).

    Entries are typically tuples of the form: (priority number, data).
    """

    def __init__(self, maxsize: int = 0) -> None:
        super().__init__(maxsize)
        self._getter_timer: Optional[TimerHandle] = None

    def _init(self, maxsize: int):
        self._queue: list[tuple[float, CalendarEvent]] = []

    def _update_timer(self):

        if self.empty():
            # make sure we cancel the timer if present
            if self._getter_timer:
                self._getter_timer.cancel()
            # delete the timer, nothing scheduled so far
            self._getter_timer = None
            return

        # peek the next timestamp
        ts = self._queue[0][0]

        loop = self._get_loop()

        if self._getter_timer is None:
            self._getter_timer = loop.call_later(ts - time(), self._calendar_alarm)
            return

        prev_timer_ts = self._getter_timer.when()
        if self.qsize() > 1 and prev_timer_ts > loop.time():
            should_update = not math.isclose(
                prev_timer_ts, loop.time() + ts - time(), abs_tol=0.00001
            )
        else:
            should_update = True

        if should_update:
            self._getter_timer.cancel()
            # ask the loop to call the alarm (_wakeup_next) at the timestamp
            self._getter_timer = loop.call_later(ts - time(), self._calendar_alarm)

    def _calendar_alarm(self):
        self._wakeup_next(self._getters)

    def _put(self, item: tuple[float, CalendarEvent], heappush=heap_push):
        heappush(self._queue, (item))
        self._update_timer()

    def _get(self, heappop=heap_pop):
        item = heappop(self._queue)
        self._update_timer()
        return item

    async def get(self) -> tuple[float, CalendarEvent]:
        """Remove and return an item from the queue.

        If queue is empty, wait until an item is available.

        Raises:
            QueueShutDown: (Only in python >= 3.13) if the queue has been
                shut down and is empty, or if the queue has been shut down
                immediately.

        Returns:
            (Tuple[float, CalendarEvent]): Tuple containing the scheduled
                timestamp and the event.
        """

        # we should await if the queue is empty or if the timer
        # is scheduled in the future w.r.t the current timestamp
        if self.empty() or (
            self._getter_timer is not None
            and self._getter_timer.when() > self._get_loop().time()
        ):

            if getattr(self, "_is_shutdown", False) and self.empty():
                raise QueueShutDown

            getter = self._get_loop().create_future()
            self._getters.append(getter)
            try:
                await getter
            except Exception:
                getter.cancel()  # Just in case getter is not done yet.
                try:
                    # Clean self._getters from canceled getters.
                    self._getters.remove(getter)
                except ValueError:
                    # The getter could be removed from self._getters by a
                    # previous put_nowait call.
                    pass
                if (
                    self._getter_timer
                    and self._getter_timer.when() < self._get_loop().time()
                    and not getter.cancelled()
                ):
                    # We were woken up by put_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._getters)
                raise

        return self.get_nowait()

    async def put(self, item: tuple[Union[float, int], CalendarEvent]) -> None:
        """Put an item into the queue.

        Put an item into the queue. If the queue is full, wait until a free
        slot is available before adding item.

        Args:
            item (tuple[Union[float, int], CalendarEvent]): Item to put in the queue.
        
        Raises:
            QueueShutDown: (Only in python >= 3.13) if the queue has been
                shut down.
        """
        while self.full():
            if getattr(self, "_is_shutdown", False):
                raise QueueShutDown
            putter = self._get_loop().create_future()
            self._putters.append(putter)
            try:
                await putter
            except Exception:
                putter.cancel()  # Just in case putter is not done yet.
                try:
                    # Clean self._putters from canceled putters.
                    self._putters.remove(putter)
                except ValueError:
                    # The putter could be removed from self._putters by a
                    # previous get_nowait call.
                    pass
                if not self.full() and not putter.cancelled():
                    # We were woken up by get_nowait(), but can't take
                    # the call.  Wake up the next in line.
                    self._wakeup_next(self._putters)
                raise
        return self.put_nowait(item)

    def put_nowait(self, item: tuple[Union[float, int], CalendarEvent]):
        """Put an item into the queue without blocking.

        If no free slot is immediately available, raise QueueFull.

        Args:
            item (tuple[Union[float, int], CalendarEvent]): Item to put in the queue

        Raises:
            QueueFull: when queue is full.
            QueueShutDown: (Only in python >= 3.13) if the queue has been shut down.
        """
        if getattr(self, "_is_shutdown", False):
            raise QueueShutDown
        if self.full():
            raise QueueFull
        self._put(item)
        self._unfinished_tasks += 1
        self._finished.clear()

    def next_in(self) -> Optional[float]:
        """Get the seconds left until the next scheduled event. If the
        event is overdue it returns 0. None is returned in case there are no
        scheduled events.

        Returns:
            (Optional[float]): Seconds left until the next scheduled event
        """
        if self._getter_timer is None:
            return None
        when = self._getter_timer.when()
        secs_left = when - self._get_loop().time()

        if secs_left < 0:
            return 0

        return secs_left

    def peek(self) -> Optional[CalendarEvent]:
        """Peek the next scheduled item in the queue.

        Returns:
            (Optional[CalendarItem]): The next scheduled item, None if the queue
                is empty.
        """
        if self.qsize() == 0:
            return None

        return self._queue[0][-1]

    def delete_items(
        self, selector: Callable[[tuple[float, CalendarEvent]], bool]
    ) -> list[tuple[float, CalendarEvent]]:
        """Delete selected items from the queue.

        Items are selected using the selector function.

        Args:
            selector (Callable[[tuple[float, CalendarEvent]], bool]): Selector
                function that takes a tuple as arg in the form of
                (scheduled_ts, key, item). The function should return True if
                the item is supposed to be deleted from the queue, False otherwise.

        Returns:
            (list[tuple[float, CalendarEvent]]): List containing deleted items
        """
        del_items: list[tuple[float, CalendarEvent]] = []
        q_len = self.qsize()
        for i, item in enumerate(reversed(self._queue)):
            if selector(item):
                del_items.append(self._queue.pop(q_len - 1 - i))

        self._update_timer()

        return del_items
