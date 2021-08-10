"""Logging handler to count the number of log messages for each level."""
import logging


class LogCounterHandler(logging.Handler):
    """Logging handler to count the number of log messages for each level."""

    def __init__(self, *args, **kwargs):
        super(LogCounterHandler, self).__init__(*args, **kwargs)
        self.level_to_count = {}

    def emit(self, record):
        """
        Override for the emit method called when logging.

        @param logging.record record
        """
        level = record.levelname

        if level not in self.level_to_count:
            self.level_to_count[level] = 0

        self.level_to_count[level] += 1
