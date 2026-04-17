# Calendar Tutorial

`Calendar` is a small helper around `CalendarQueue` that accepts `datetime`
objects and exposes an async iterator. The examples below show common patterns
for scheduling, inspecting, cancelling and running scheduled work.

```python
from datetime import datetime, timedelta
from calendar_queue import Calendar

calendar = Calendar()
```

## Schedule reminders

Schedule a few reminders a few seconds apart:

```python
calendar.schedule("Pay bills", when=datetime.now() + timedelta(seconds=3))
calendar.schedule("Stretch", when=datetime.now() + timedelta(seconds=6))
calendar.schedule("Stand up", when=datetime.now() + timedelta(seconds=9))
```

## Inspect next event

Peek the next scheduled event and how long until it fires:

```python
next_item = calendar.next_scheduled()
time_left = calendar.time_remaining()
```

## Cancel a specific event

Cancel any events matching a predicate (for example, cancel all reminders named
"Stretch"):

```python
deleted = calendar.cancel_event(lambda item: item[1] == "Stretch")
```

## Run the calendar

Consume scheduled events using the async iterator; this is the simplest way to
process items as they become due.

```python
import asyncio

async def run():
    async for ts, event in calendar:
        print(f"{datetime.fromtimestamp(ts).isoformat()}: {event}")
        if event == "Stand up":
            calendar.stop()

asyncio.run(run())
```

## Clear everything

To remove all scheduled events use `clear()`:

```python
calendar.clear()
```

These examples are intentionally small and focused. Combine scheduling and
consumption patterns to fit your application's concurrency model.
