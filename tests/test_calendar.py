import math
from datetime import datetime, timedelta
from time import time

import pytest

from calendar_queue import Calendar, CalendarMissingExecutor
from tests import ABS_TOLERANCE

MyItem = tuple[str, int]


@pytest.mark.asyncio
async def test_init():

    c: Calendar[MyItem] = Calendar()

@pytest.mark.asyncio
async def test_schedule():

    c: Calendar[str] = Calendar()

    ts = datetime.now() + timedelta(seconds=10)

    c.schedule("foo", ts)

    assert c.next_scheduled() == "foo" and math.isclose(c.time_remaining(), ts.timestamp() - time(), abs_tol=ABS_TOLERANCE)

    c.clear()

    c.schedule("bar", ts.timestamp())

    assert c.next_scheduled() == "bar" and math.isclose(c.time_remaining(), ts.timestamp() - time(), abs_tol=ABS_TOLERANCE)


@pytest.mark.asyncio
async def test_events_generator():

    c: Calendar[int] = Calendar()

    ts = datetime.now()

    for i in range(5):
        c.schedule(i, ts + timedelta(seconds=i * 1))

    count = 0
    async for ts, event in c.events():
        assert (time() >= ts or math.isclose(time(), ts)) 
        assert event == count
        count += 1

        if count == 5:
            c.stop()


@pytest.mark.asyncio
async def test_run_async_executor():

    c: Calendar[int] = Calendar()

    ts = datetime.now()

    for i in range(5):
        c.schedule(i, ts + timedelta(seconds=i * 1))

    count = 0

    async def async_executor(ts, item, calendar):
        nonlocal count

        assert (time() >= ts or math.isclose(time(), ts)) 
        assert item == count
        assert calendar == c

        count += 1

        if count == 5:
            c.stop()

    with pytest.raises(CalendarMissingExecutor):
        await c.run()
    
    c.set_executor(executor=async_executor)

    await c.run()

    assert count == 5


@pytest.mark.asyncio
async def test_run_executor():

    c: Calendar[int] = Calendar()

    ts = datetime.now()

    for i in range(5):
        c.schedule(i, ts + timedelta(seconds=i))

    c.schedule(5, ts + timedelta(seconds=4))

    count = 0
    test_done = False

    def executor(ts, item, calendar):
        nonlocal count
        nonlocal test_done

        assert (time() >= ts or math.isclose(time(), ts)) 
        assert item == count
        assert calendar == c

        count += 1

        if count >= 5:
            if not test_done:
                test_done = True
            
            c.stop()

    
    with pytest.raises(CalendarMissingExecutor):
        await c.run()
    
    c.set_executor(executor=executor)

    await c.run()

    assert count == 5

    await c.run()

    assert count == 6

    
@pytest.mark.asyncio
async def test_cancel_events():

    c: Calendar[int] = Calendar()

    ts = datetime.now()

    for i in range(5):
        c.schedule(i, ts + timedelta(seconds=i * 1))
    
    len(c.remaining_events()) == 5

    pick_events = lambda x: x[1] % 2

    cancelled_events = c.cancel_event(pick_events)

    assert (len(cancelled_events) == 2 and 
            all(pick_events(x) for x in cancelled_events))
    
    remaining_events = c.remaining_events()

    assert (len(remaining_events) == 3 and
            all(not pick_events(x) for x in remaining_events))

    async for ts, event in c.events():
        assert (time() >= ts or math.isclose(time(), ts)) 
        assert not event % 2

        if len(c.remaining_events()) == 0:
            c.stop()
