# Calendar Queue Tutorial

`CalendarQueue` is a [PriorityQueue](https://docs.python.org/3/library/asyncio-queue.html#priority-queue) in which the priority of each queued element (i.e. event) is the unix timestamp of the event. While using the `Calendar` class is much easier, here are some possible usages of `CalendarQueue`. 

## The Event

In a priority queue each element inserted must be comparable with the other so that they can be ordered. In python this translates as each item must implement the `__lt__` method for comparing two elements. To create items with several components, the simplest thing is to create a tuple, however be mindful so that at least one of the tuple elements is guaranteed to be unique, otherwise they cannot be ordered and therefore the priority will break.

If you need to use complex elements you can create your own class that implements `__lt__` as well or follow [python's documentation suggestion and use a dataclass that ignores the data item and only compares the priority number](https://docs.python.org/3/library/queue.html#queue.PriorityQueue).

The `CalendarQueue` class supports type hints so you can define your own type and then use as:
```python

# simplest case using tuple
MyCustomEventType = tuple[str, str] # example: ("foo", "bar")

# complex event
class MyComplexEventType:

    def __init__(self, ...):
        ...

    def __lt__(self, other) -> bool:

        # do your comparison
        return True # True/False

# use it
cq: CalendarQueue[MyComplexEventType] = CalendarQueue()
```

## Check the next events

Conveniently the time remaining to the next event can be checked using `next_in`. It the number of seconds remaining until the next events, otherwise returns `None` if no events are scheduled:

```python

time_remaining = cq.next_in()

if time_remaining is not None:
    print(f"{time_remaining} seconds remaining until the next scheduled event")
else:
    print("No scheduled events")

```

You can also peek the next event by using `peek`:

```python
next_event = cq.peek()

if next_event:
    print(f"Next event is {next_event}")
else:
    print("No upcoming events")
```

## Deleting events

In case cancelling an event is needed, the `delete_items` method can be used. It needs as argument a callable function that receives the tuple `(timestamp, event)` and returns `True` if the element should be deleted, `False` otherwise. 
Suppose we would like to cancel all events that are scheduled to happen in the next 5 minutes:

```python

now = time.time()

deadline = now + 300 # now + 5 mins

def event_selector(item: tuple[int, Any]):

    ts, event = item

    if ts <= deadline:
        return True
    
    return False

cancelled_events = cq.cancel_events(event_selector)

for ts, ev in cancelled_events:
    # do some checks on the cancelled events
    ...

```

## Example usage

A full example usage of `CalendarQueue` that involves two (or more) asyncio Tasks following the producer-consumer pattern.

Suppose we handle a take away restaurant, we gather the orders and the kitchen needs to cook the meals for the requested time for the customers to pick them up. To do so, we have:

1. producer tasks that would be the persons responsible for taking the orders
2. consumer tasks that would be the cooks

The consumer tasks will be triggered only at the scheduled time (we want to cook the meals when they need to be picked up, not when we receive the order!).

```python
import asyncio
from datetime import datetime, timedelta
from random import choice, choices, randint, randrange
from secrets import token_hex

from calendar_queue import CalendarQueue

# Let's define what's a meal order
Order = tuple[int, str, list] # (order id, customer name, meals)

# use the low level calendar queue
cq: CalendarQueue[Order] = CalendarQueue()

first_names = ["Clara", "John", "Dave", "Julia"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]

meals = ["pasta", "pizza", "ramen", "hamburger", "dahl", "pad thai"]

# order id counter
id_count = 0

def get_customer_name() -> str:
    """Create random customer name"""

    return f"{choice(first_names)} {choice(last_names)}"

def get_ordered_meal() -> list[str]:
    """Create random meal order"""

    n_meals = randint(1, 5)
    return choices(meals, k=n_meals)

async def get_order():
    """Wait for a customer call and put the new order in the queue"""

    while True:

        print("Waiting for a call..")

        await asyncio.sleep(randint(1, 5))

        # hello sir/madame, what's your name?
        customer_name = get_customer_name()

        # what would you like to order?
        ordered_meal = get_ordered_meal()

        # at which time will you pick it up?
        scheduled_ts = datetime.now() + timedelta(seconds=randrange(5, 10))

        global id_count
        id_count += 1

        # create a unique order id
        order_id = id_count

        print(f"Got a call from {customer_name}, order id {order_id}. "
              f"Ordered {ordered_meal} to be picked up at {scheduled_ts.isoformat()}")

        # put together the order
        customer_order: Order = (order_id, customer_name, meals)

        # put the order in the queue, no need to wait, the queue has no size
        cq.put_nowait((scheduled_ts.timestamp(), customer_order))


async def wait_for_order_to_be_prepared():
    """This is the kitchen, wait for the right moment to start preparing the meals"""

    while True:
        try:
            ts, el = await cq.get()
        except KeyboardInterrupt:
            break

        print(f"{datetime.now().isoformat()}: preparing {el} "\ 
              f"scheduled for {datetime.fromtimestamp(ts).isoformat()}")

async def main():

    await asyncio.gather(import asyncio
from datetime import datetime
from random import randrange
from secrets import token_hex

from calendar_queue import CalendarQueue

# let's define what's a meal order
Order = tuple[str, str, list] # (order id, customer name, meals)

# create a CalendarQueue instance
cq: CalendarQueue[Order] = CalendarQueue()


async def put_random():

    print("Waiting 3 seconds before starting to put")

    await asyncio.sleep(3)

    print("Wait completed, done")

    while True:

        await asyncio.sleep(1)

        scheduled_ts = datetime.now().timestamp() + randrange(1, 5)

        s = token_hex(8)

        current_item: CustomItem = (s)

        print(f"{datetime.now().isoformat()}: putting {current_item} scheduled for {datetime.fromtimestamp(scheduled_ts).isoformat()}")

        cq.put_nowait((scheduled_ts, current_item))
        asyncio.create_task(get_order()),
        asyncio.create_task(wait_for_order_to_be_prepared()),
    )


if __name__ == "__main__":
    asyncio.run(main())
```
 