# Changelog

## [0.2.1] - 2026-04-18

### Fixed

- Restore heap invariant in `CalendarQueue.delete_items()` by calling `heapq.heapify(self._queue)` after removing items; prevents incorrect ordering after arbitrary deletions.

### Added

- Regression test `test_delete_restores_heap_property` in `tests/test_calendar_queue.py` covering deletion + heap restore behavior.

## [0.2.0] - 2026-01-01

### Changed

- **Breaking Change**: Removed the executor pattern from `Calendar` class. The `executor` attribute and the `run()` method are no longer available.
- **Breaking Change**: `Calendar.events()` method returns the list of queued events. The async iterator is now implemented within the `Calendar` class (`__aiter__` and `__anext__`). The `Calendar` class can now be used directly in `async for` loops.
- **Breaking Change**: The queue is no longer automatically cleared before starting to iterate over events. Previously, calling the async iterator would clear any pending events; now existing events are preserved.

### Updated

- Updated all documentation examples to use the new async iterator interface
- Updated tutorial examples to demonstrate the new `async for` usage pattern with `Calendar`
- Updated test suite to reflect the new async iterator implementation
- Added support for Python 3.14
- Updated CI/CD workflows for Python 3.14 compatibility
- Updated development dependencies

### Migration Guide

**Before (v0.1.0):**

```python
async for ts, event in calendar.events():
    # handle event
```

**After (v0.2.0):**

```python
async for ts, event in calendar:
    # handle event
```

## [0.1.0] - Previous Release

Initial `calendar-queue` release.
