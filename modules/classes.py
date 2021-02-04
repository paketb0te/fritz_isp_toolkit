"""
Module containing classes for use in the friitz_isp_toolit
"""

import dateparser


class LogEntry:  # pylint: disable=too-few-public-methods
    """
    A basic class containing a timestamp and the message of a log entry
    """

    def __init__(self, logstring: str, msg_offset=18) -> None:
        self.timestamp = dateparser.parse(logstring[:msg_offset])

        self.message = logstring[msg_offset:].strip()

    def __str__(self):
        # return the timestamp and local timezone info in ISO 8601 representation
        return f"{self.timestamp.astimezone().isoformat()} {str(self.message)}"


class Notifier:  # pylint: disable=too-few-public-methods
    """
    Abstract base class for the different notifiers
    """

    def __init__(self, isp_address: str, new_entries: list) -> None:
        self.isp_address = isp_address
        self.new_entries = new_entries

    def notify(self) -> None:
        """Abstract method for notifying via different channels

        Raises:
            NotImplementedError: Each child-class has to implment its own 'notify' function
        """
        raise NotImplementedError("Subclass must implement abstract method 'notify'")
