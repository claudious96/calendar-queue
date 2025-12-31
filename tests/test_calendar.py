from datetime import datetime, timedelta
from time import time

import pytest

from calendar_queue import Calendar
from tests import ABS_TOLERANCE

MyItem = tuple[str, int]


@pytest.mark.asyncio
async def test_init():
    """Test initializing a Calendar"""

    c: Calendar[MyItem] = Calendar()


@pytest.mark.asyncio
async def test_schedule():
    """Test scheduling an event result in having a the correct event
    scheduled as next and at the correct time.
    """

    c: Calendar[str] = Calendar()

    ts = datetime.now() + timedelta(seconds=10)

    c.schedule("foo", ts)

    # check that the next in line is the correct one and that the time remaining is approximately the same (can't check exact)
    assert c.next_scheduled() == "foo" and c.time_remaining() == pytest.approx(ts.timestamp() - time(), abs=ABS_TOLERANCE)

    c.clear()

    c.schedule("bar", ts.timestamp())

    # check that the next in line is the correct one and that the time remaining is approximately the same (can't check exact)
    assert c.next_scheduled() == "bar" and c.time_remaining() == pytest.approx(ts.timestamp() - time(), abs=ABS_TOLERANCE)


@pytest.mark.asyncio
async def test_events_generator():
    """Test that the events generator yields event at the correct time
    and in the correct order.
    """

    c: Calendar[int] = Calendar()

    ts = datetime.now()

    # add some elements
    for i in range(5):
        c.schedule(i, ts + timedelta(seconds=i * 1))

    count = 0
    async for ts, event in c:
        # ensure events are yielded at the right time
        assert time() >= ts or time() == pytest.approx(ts)
        assert event == count
        count += 1

        if count == 2:
            # cancel an event, make sure it is cancelled
            # so that we can test that the generator
            # works correctly when events are cancelled
            # while it's being used.
            ce = c.cancel_event(lambda x: x[1] == 2)
            assert len(ce) == 1
            # increase the count so that the checks
            # that are based on the index can pass
            # (we removed the next one)
            count += 1

        if count == 5:
            assert len(c.events()) == 0
            c.stop()


@pytest.mark.asyncio
async def test_cancel_events():
    """Test that cancelling events remove them from the calendar
    and that the next in line is correctly scheduled"""

    c: Calendar[int] = Calendar()

    ts = datetime.now()

    for i in range(5):
        c.schedule(i, ts + timedelta(seconds=i * 1))

    assert len(c.events()) == 5

    pick_events = lambda x: x[1] % 2

    cancelled_events = c.cancel_event(pick_events)

    assert len(cancelled_events) == 2 and all(pick_events(x) for x in cancelled_events)

    remaining_events = c.events()

    assert len(remaining_events) == 3 and all(
        not pick_events(x) for x in remaining_events
    )

    async for ts, event in c:
        assert time() >= ts or time() == pytest.approx(ts)
        assert not event % 2

        if len(c.events()) == 0:
            c.stop()
