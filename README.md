# calendar-queue

[![PyPI pyversions](https://img.shields.io/pypi/pyversions/calendar-queue.svg)](https://pypi.python.org/pypi/calendar-queue/)
![tests](https://github.com/claudious96/calendar-queue/actions/workflows/pytest.yml/badge.svg?branch=main)
![linting](https://github.com/claudious96/calendar-queue/actions/workflows/pylint.yml/badge.svg?branch=main)
[![codecov](https://codecov.io/gh/claudious96/calendar-queue/graph/badge.svg?token=XWB9F7N11E)](https://codecov.io/gh/claudious96/calendar-queue)

A pure-python [calendar queue](https://en.wikipedia.org/wiki/Calendar_queue) and library for scheduling events with [`asyncio`](https://docs.python.org/3/library/asyncio.html).

Many other libraries allow for event/job scheduling but either they are not asynchronous or they are just fire-and-forget.
`calendar-queue` has two purposes:

1. providing the primitives for creating your own scheduler by exporting a `CalendarQueue` class in which events can be awaited
2. providing a higher level abstraction `Calendar` class that simplifies the usage of `CalendarQueue`.

Depending on your needs, you can use one of the two to develop your own event manager/scheduler. 

The idea is: we take care of emitting events at the right time, you write the logic for acting accordingly.

## Install

```bash
pip install calendar-queue
```

## Usage

An example usage of `CalendarQueue`

```python
import asyncio
from datetime import datetime
from random import randrange
from secrets import token_hex

from calendar_queue import CalendarQueue

# (optional) define the item type 
CustomItem = tuple[str]

# use the low level calendar queue
cq: CalendarQueue[CustomItem] = CalendarQueue()

async def put_random():

    print("Putting new items in the calendar queue. Hit CTRL + C to stop.")

    while True:

        # sleep for a while, just to release the task
        await asyncio.sleep(1)

        scheduled_ts = datetime.now().timestamp() + randrange(1, 5)

        s = token_hex(8)

        current_item: CustomItem = (s)

        print(f"{datetime.now().isoformat()}: putting {current_item} scheduled for {datetime.fromtimestamp(scheduled_ts).isoformat()}")

        cq.put_nowait((scheduled_ts, current_item))


async def get_from_queue():

    while True:
        ts, el = await cq.get()

        print(f"{datetime.now().isoformat()}: getting {el} scheduled for {datetime.fromtimestamp(ts).isoformat()}")

async def main():

    await asyncio.gather(
        asyncio.create_task(put_random()),
        asyncio.create_task(get_from_queue()),
    )


if __name__ == "__main__":
    asyncio.run(main())    

```

## Development

This library is developed using Python 3.11 and [`pdm`](https://pdm-project.org/en/latest/) as dependency manager.

Testing is done via github actions and it's done on python versions `3.10`, `3.11`, `3.12` and on latest `ubuntu`, `macos`, `windows` OSes.

For local development you'll need to have pdm installed, then you can:

1. run `pdm install` to create the virtual environment and install the dependencies
1. run `pdm venv activate` to activate the virtual environment
1. run the tests using `pytest`
1. run the linter `pylint src`

## Contributing

Contributions are welcome! Especially for new tests and for improving documentation and examples.

## License

The code in this project is released under the [MIT License](LICENSE).
