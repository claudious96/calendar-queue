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

## Quickstart

A minimal, practical example showing how `Calendar` can schedule and emit events: schedule three reminders a few seconds apart and consume them as they fire.

```python
import asyncio
from datetime import datetime, timedelta
from calendar_queue import Calendar

calendar = Calendar()

async def producer():
    for i in range(1, 4):
        when = datetime.now() + timedelta(seconds=i * 2)
        calendar.schedule(f"Reminder {i}", when=when)
        print(f"scheduled Reminder {i} for {when.isoformat()}")
        await asyncio.sleep(0.1)

async def consumer():
    async for ts, event in calendar:
        print(f"{datetime.fromtimestamp(ts).isoformat()}: {event}")
        # stop after the last event
        if event == "Reminder 3":
            calendar.stop()

async def main():
    await asyncio.gather(producer(), consumer())

if __name__ == "__main__":
    asyncio.run(main())
```

For more examples and the API reference, see the documentation in the `docs` folder:

- Tutorials: [docs/tutorials](docs/tutorials/)
- API reference: [docs/api-reference](docs/api-reference/)

## Development

This library is developed using Python 3.11 and [`pdm`](https://pdm-project.org/en/latest/) as dependency manager.

Testing is done via github actions and it's done on python versions `3.10`, `3.11`, `3.12`, `3.13`, `3.14`, `3.14t` and on latest `ubuntu`, `macos`, `windows` OSes.

For local development you'll need to have pdm installed, then you can:

1. run `pdm install` to create the virtual environment and install the dependencies
1. run `pdm venv activate` to activate the virtual environment
1. run the tests using `pytest`
1. run the linter `pylint src`

## Contributing

Contributions are welcome! Especially for new tests and for improving documentation and examples.

## License

The code in this project is released under the [MIT License](LICENSE).
