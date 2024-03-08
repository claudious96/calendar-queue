"""Define exceptions for calendar_queue"""


class CalendarMissingExecutor(Exception):
    """Exception raised when run is called but no executor
    function is set in the Calendar instance.
    """
