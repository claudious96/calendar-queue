# Calendar Tutorial

`Calendar` is an utility class made for simplify the usage of `CalendarQueue`. Just like `CalendarQueue`, `Calendar` support type hints and the event type can be set when initializing the calendar:

```python

MyEvent = tuple[str, str]

calendar: Calendar[MyEvent] = Calendar()

```

## Scheduling an event

Scheduling an event can be done via the `schedule` method:

```python

event = ("my", "event")

# ts can be also a float/int
ts = datetime.now() + timedelta(hours=2)

calendar.schedule(item=event, when=ts)

```

## Checking scheduled events

Scheduled events can be checked using the methods:

1. `next_scheduled`: to get the next scheduled event, None if there are no scheduled events
1. `time_remaining`: to get the time (seconds) remaining to the next event, None if there are no scheduled events
1. `remaining_events`: to get all remaining scheduled events

### Cancelling an event

To cancel one (or more) events, the `cancel_event` method can be used, passing a selector function as arg:

```python

now = time.time()

deadline = now + 300 # now + 5 mins

def event_selector(item: tuple[int, Any]):

    ts, event = item

    if ts <= deadline:
        return True

    return False

cancelled_events = calendar.cancel_event(event_selector)

for ts, ev in cancelled_events:
    # do some checks on the cancelled events
    ...

```

## Cancelling all events

To cancel all events the `clear` method can be used:

```python

# all events will be cleared
calendar.clear()

```

## Running the calendar

Now that we know how to schedule events, we need to consume the events as they happen which can be done using the class as an asynchronous generator which yields a tuple of `timestamp` and `Event` as they are released from the internal calendar queue.

```python

async for ts, event in calendar:

    # do stuff with the emitted events

```
