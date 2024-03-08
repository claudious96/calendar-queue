# Calendar Queue

A pure-python [calendar queue](https://en.wikipedia.org/wiki/Calendar_queue) and library for scheduling events with [`asyncio`](https://docs.python.org/3/library/asyncio.html).

Many other libraries allow for event/job scheduling but either they are not asynchronous or they are just fire-and-forget.
Calendar Queue has two purpose:

1. providing the primitives for creating your own calendar by exporting a `CalendarQueue` class in which events can be awaited
2. providing a higher level abstraction `Calendar` class that simplifies the usage of `CalendarQueue`.

Depending on your needs, you can use one of the two to develop your own event manager (calendar). 

The idea is: we take care of emitting events at the right time, you write the logic for acting accordingly.


## Install

Required python >= 3.10 

```bash
pip install calendar-queue
```
