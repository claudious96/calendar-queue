# Calendar Queue Tutorial

`CalendarQueue` is an asyncio-friendly priority queue where each item is a
tuple whose priority is the unix timestamp when the item should be emitted.
Below are concise, practical examples showing correct and idiomatic usage.

## Basic rules

- Each queued item should be comparable or wrapped in a tuple `(timestamp, item)`.
- Use `put_nowait((ts, item))` to schedule; use `await get()` to receive the next
  scheduled item when its time has come.

## Producer / consumer example

This small example demonstrates a producer that schedules short jobs and a
consumer that processes them when their scheduled time arrives.

```python
import asyncio
from datetime import datetime
from random import randrange

from calendar_queue import CalendarQueue

cq = CalendarQueue()

async def producer(n=5):
    for i in range(1, n + 1):
        # schedule each job 1..5 seconds from now
        ts = datetime.now().timestamp() + randrange(1, 6)
        cq.put_nowait((ts, f"job-{i}"))
        print(f"scheduled job-{i} for {datetime.fromtimestamp(ts).isoformat()}")
        await asyncio.sleep(0.1)

async def consumer(total=5):
    received = 0
    while received < total:
        ts, job = await cq.get()
        print(f"{datetime.now().isoformat()}: running {job} scheduled for {datetime.fromtimestamp(ts).isoformat()}")
        received += 1

async def main():
    await asyncio.gather(producer(), consumer())

if __name__ == "__main__":
    asyncio.run(main())
```

## Inspecting and cancelling

You can peek the next item with `peek()` and see the seconds until it fires
with `next_in()`:

```python
next_event = cq.peek()
time_left = cq.next_in()
```

To remove scheduled items, use `delete_items(selector)` passing a selector
callable that returns `True` for items you want removed. For example, remove all
items scheduled within the next 5 minutes:

```python
import time

deadline = time.time() + 300
deleted = cq.delete_items(lambda item: item[0] <= deadline)
```

This file focuses on `CalendarQueue` primitives. For easier datetime-based
usage prefer the `Calendar` helper (see the `Calendar` tutorial).
