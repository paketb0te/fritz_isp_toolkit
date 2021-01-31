"""
Module containing classes for use in the friitz_isp_toolit
"""
import dateparser


class LogEntry:
    """
    A basic class containing a timestamp and the message of a log entry
    """

    def __init__(self, logstring: str, msg_offset=18) -> None:
        self.timestamp = dateparser.parse(logstring[:msg_offset])

        self.message = logstring[msg_offset:].strip()

    def __str__(self):
        return str(self.timestamp) + " " + str(self.message)