"""
Module containing notifiers for the fritz_isp_toolkit 
"""

# Import modules
from classes import LogEntry


def print_to_stdout(isp_address: str, new_entries: list()) -> None:
    """
    Notifier printing information about the new entries to stdout.
    """
    if new_entries:
        print("-" * 80)
        print(f"{len(new_entries)} new log entries on {isp_address}:\n")
        for entry in new_entries:
            print(entry)
        print("-" * 80)
    else:
        print("-" * 80)
        print(f"Now new entries on {isp_address}.")
        print("-" * 80)
