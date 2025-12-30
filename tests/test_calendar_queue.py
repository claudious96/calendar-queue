import asyncio
import sys
from datetime import timedelta
from time import time
from unittest.mock import patch

import pytest

from calendar_queue import CalendarQueue
from tests import ABS_TOLERANCE


def test_init():

    assert CalendarQueue()


@pytest.mark.asyncio
@pytest.mark.skipif(
    sys.version_info < (3, 13),
    reason="Queue shutdown is supported only from python 3.13 on",
)
async def test_queue_shutdown():
    """Test for python >= 3.13 only. Check that QueueShutDown
    is correctly raised when putting or getting after shutting down the queue
    """

    from asyncio import QueueShutDown # type: ignore

    cq = CalendarQueue()

    cq.shutdown() # type: ignore

    with pytest.raises(QueueShutDown):
        await cq.get()

    with pytest.raises(QueueShutDown):
        await cq.put((time() + 10, "foo"))


@pytest.mark.asyncio
async def test_simple_put():
    """Test put by putting one element and checking that
    the it is present in the queue and verifying that the
    timer is correctly set for the given timestamp
    """

    cq = CalendarQueue()

    base_ts = time()

    base_loop_ts = cq._get_loop().time() # type: ignore

    ts_1 = base_ts + 10

    foo = (ts_1, "foo")

    await cq.put(item=foo)

    assert cq.peek() == foo[-1]

    assert cq._getter_timer is not None

    # check timer is correct (we can't match the exact timestamp)
    assert cq._getter_timer.when() == pytest.approx(base_loop_ts + 10, abs=ABS_TOLERANCE)

    ts_2 = base_ts + 5

    bar = (ts_2, "bar")

    cq.put_nowait(item=bar)

    assert cq.peek() == bar[-1]

    # check timer is correct (we can't match the exact timestamp)
    assert cq._getter_timer.when() == pytest.approx(base_loop_ts + 5, abs=ABS_TOLERANCE)


@pytest.mark.asyncio
async def test_get():
    """Test getting an element by putting one, getting it and
    checking that the time at which it is returned is correct.
    """

    cq = CalendarQueue()

    foo = (time() + 1, "foo")

    await cq.put(item=foo)

    # check timer is correct (we can't match the exact timestamp)
    assert (await cq.get()) == foo and (
        time() >= foo[0] or time() == pytest.approx(foo[0])
    )


@pytest.mark.asyncio
async def test_delete_items():
    """Test the routing for deleting the items by inserting
    a set of numbers, purging only the odd entries
    and then checking the number of remaining elements.
    """

    cq = CalendarQueue()

    for i in range(10):
        cq.put_nowait((time() + 60, f"{i}"))

    cq.delete_items(lambda x: bool(int(x[-1]) % 2))

    assert cq.qsize() == 5


@pytest.mark.asyncio
async def test_far_schedule():
    """Test putting an event scheduled far in time.
    We use LoopTimeTravel to simulate the time traveling
    and verify that the elements are returned at the correct
    timestamp.
    """

    cq = CalendarQueue()

    cq_loop = cq._get_loop() # type: ignore

    delta = timedelta(days=30)

    cq.put_nowait((time() + delta.total_seconds(), "foo"))

    with pytest.raises((TimeoutError, asyncio.TimeoutError)):
        await asyncio.wait_for(cq.get(), 2)
        pytest.fail("Item was returned immediately. It makes no sense.")

    with patch.object(cq_loop, "time", return_value=cq_loop.time() + delta.total_seconds() + 10):
        item = await asyncio.wait_for(cq.get(), 5)
        assert item[-1] == "foo"


@pytest.mark.asyncio
async def test_put():
    """Another test for put, this time we put events scheduled
    for several timestamp, willingly in an unordered fashion
    and each time verify that the timer for returning the next
    event is correctly updated.
    """

    cq_nosize = CalendarQueue()

    base_ts = time()
    base_loop_ts = cq_nosize._get_loop().time() # type: ignore

    await cq_nosize.put((base_ts + 180, "foo"))

    assert cq_nosize._getter_timer is not None

    # check timer is correct (we can't match the exact timestamp)
    assert cq_nosize._getter_timer.when() == pytest.approx(base_loop_ts + 180, abs=ABS_TOLERANCE)

    await cq_nosize.put((base_ts + 300, "bar"))

    # check timer is correct (we can't match the exact timestamp)
    assert cq_nosize._getter_timer.when() == pytest.approx(base_loop_ts + 180, abs=ABS_TOLERANCE)

    await cq_nosize.put((base_ts + 90, "baz"))

    # check timer is correct (we can't match the exact timestamp)
    assert cq_nosize._getter_timer.when() == pytest.approx(base_loop_ts + 90, abs=ABS_TOLERANCE)

    assert cq_nosize.qsize() == 3


@pytest.mark.asyncio
async def test_put_limited_q():
    """Test putting elements in a CalendarQueue with maxsize set."""

    cq = CalendarQueue(1)

    base_ts = time()

    first_ts = base_ts + 2
    second_ts = base_ts + 4

    await cq.put((first_ts, "foo"))

    with pytest.raises(asyncio.QueueFull):
        cq.put_nowait((base_ts, "dummy"))
        pytest.fail("Put an item while queue was full")

    assert cq.full()

    assert cq.qsize() == 1

    async def put_item():

        assert cq.full()

        with pytest.raises((TimeoutError, asyncio.TimeoutError)):
            await asyncio.wait_for(cq.put((second_ts, "bar")), first_ts - time() - 0.1)
            pytest.fail("Returned immediately while queue was full")

        await asyncio.wait_for(cq.put((second_ts, "bar")), first_ts - time() + 0.5)

    async def get_queue():

        ts, item = await asyncio.wait_for(cq.get(), first_ts - time() + 0.5)
        assert (
            ts == first_ts
            and (time() >= ts or time() == pytest.approx(ts))
            and item == "foo"
        )
        ts, item = await asyncio.wait_for(cq.get(), second_ts - time() + 0.5)
        assert (
            ts == second_ts
            and (time() >= ts or time() == pytest.approx(ts))
            and item == "bar"
        )

    tasks = [
        asyncio.create_task(put_item(), name="put"),
        asyncio.create_task(get_queue(), name="get"),
    ]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

    for d in done:
        assert d.exception() is None

    assert not pending


@pytest.mark.asyncio
async def test_next_in():
    """Test for ensuring that next_in returns the time left
    until the next scheduled event is correct.
    """

    cq = CalendarQueue()

    assert cq.next_in() is None

    delta_1 = 60
    delta_2 = 2

    scheduled_ts = time() + delta_1
    base_loop_ts = cq._get_loop().time() # type: ignore

    cq.put_nowait((scheduled_ts, "foo"))

    assert cq.next_in() is not None and int(cq.next_in() or 0) == int(scheduled_ts - time())

    assert cq._getter_timer is not None

    assert cq._getter_timer.when() == pytest.approx(base_loop_ts + delta_1, abs=ABS_TOLERANCE)

    cq.put_nowait((time() + delta_2, "bar"))

    await asyncio.sleep(4)

    assert cq.next_in() == 0


@pytest.mark.asyncio
async def test_peek():
    """Test to make sure that peek returns correctly the
    next event in the queue.
    """

    cq = CalendarQueue()

    assert cq.peek() is None

    ts_1 = time() + 60
    ts_2 = time() + 120
    ts_3 = time() + 10

    cq.put_nowait((ts_1, "foo"))
    cq.put_nowait((ts_2, "bar"))

    assert cq.peek() == "foo"

    cq.put_nowait((ts_3, "baz"))

    assert cq.peek() == "baz"


@pytest.mark.asyncio
async def test_delete():
    """Test that every time an event is deleted, the timer for
    getting the next event in the queue is correctly updated.
    """

    cq = CalendarQueue()

    base_ts = time()
    base_loop_ts = cq._get_loop().time() # type: ignore

    cq.put_nowait((base_ts + 120, "bar"))
    cq.put_nowait((base_ts + 60, "foo"))
    cq.put_nowait((base_ts + 180, "baz"))

    assert cq._getter_timer is not None

    assert cq._getter_timer.when() == pytest.approx(base_loop_ts + 60, abs=ABS_TOLERANCE)

    del_items = cq.delete_items(lambda x: x[1] == "foo")

    assert (
        len(del_items) == 1
        and del_items[0] == (base_ts + 60, "foo")
        and cq._getter_timer.when() == pytest.approx(base_loop_ts + 120, abs=ABS_TOLERANCE)
    )

    assert cq.qsize() == 2

    assert cq.peek() == "bar"

    cq.get_nowait()

    assert cq.peek() == "baz"
