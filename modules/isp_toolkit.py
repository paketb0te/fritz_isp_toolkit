#!/usr/bin/env python3
"""
Toolkit to manage Fritz Internet Router
to parse it's device logs and send notifications
via Gmail.

You can use something else to send the Gmail notification.
"""
# Import modules

import os
import os.path
import pathlib as pl
import sys
from os import environ
from notifiers import StdoutNotifier, GmailNotifier
from classes import LogEntry, Notifier
from dotenv import load_dotenv
from fritzconnection import FritzConnection


print("Commencing ISP Toolkit ...")
# Get path of the current dir under which the file is executed
dirname = os.path.dirname(os.path.abspath(__file__))
# Append sys path so that relative pathing works for input
# files and templates
sys.path.append(os.path.join(dirname))


def verify_env() -> None:
    """
    Block of code to process the ingestion of environmental
    variables
    """
    # Setup credential_dir
    cred_dir = pl.Path.cwd().joinpath(dirname, "..", "creds")
    # Get path to where environmental variables are stored and
    env_path = pl.Path.cwd().joinpath(cred_dir, ".env")
    # NOTE: This has been set to always revert to system provided environmental
    # variables, rather than what is provided in the .env file using
    # the override=False method.
    # If nothing is set on the system, the values from the .env file are used.
    load_dotenv(dotenv_path=env_path, override=False)

    # Specify a list of environmental variables
    # for usage inside script
    environment_variables = [
        "ISP_RTR_UNAME",
        "ISP_RTR_PWORD",
        "ISP_RTR_ADDRESS",
    ]
    # Iterate over environmental variables and ensure they are set,
    # if not exit the program.
    for variables in environment_variables:
        if environ.get(variables) is not None:
            print(f"Environmental variable: {variables} is set.")
        else:
            print(f"Environmental variable: {variables} is NOT set, exiting script.")
            sys.exit(1)


def load_list_from_logfile(filepath: str) -> list:
    """
    Reads log entries from a file and returns them as a list of LogeEntry objects.

    Args:
        filepath: String containing the file path of the local logfile.

    Raises:
        N/A

    Returns:
        log_entries: List of LogEntry objects
        created from the log lines in the local logfile.
    """
    try:
        with open(filepath, "r") as file:
            log_lines = file.readlines()
    except FileNotFoundError:
        log_lines = []

    log_entries = []

    for line in log_lines:
        log_entries.append(LogEntry(logstring=line, msg_offset=20))

    log_entries.sort(key=lambda entry: entry.timestamp)

    return log_entries


def append_list_to_logfile(log_entries: list, filepath: str) -> None:
    """
    Appends a list of (new) LogEntry objects to the specified logfile.

    Args:
        log_entries (list): The list of LogEntry objects to append
        filepath (str): Path to the local logfile

    Raises:
        N/A

    Returns:
        None
    """

    log_entries.sort(key=lambda entry: entry.timestamp)
    # no need to verify existence of the file:
    # mode 'a' autmatically creates it if not present
    with open(filepath, "a") as file:
        for entry in log_entries:
            file.write(str(entry) + "\n")


def get_list_from_device(conn: FritzConnection) -> list:
    """
    Fetches the logfile from the connected device
    and turns it into a list of LogEntry objects.

    Args:
        conn (FritzConnection): Connection object to connect to.

    Returns:
        log_entries (list): List of LogEntry objects created
        from the devices' logfile, sorted by timestamp.
    """

    log_dict = conn.call_action("DeviceInfo1", "GetDeviceLog")
    log_lines = log_dict.get("NewDeviceLog", "").split("\n")

    log_entries = []

    for line in log_lines:
        log_entries.append(LogEntry(logstring=line, msg_offset=18))

    log_entries.sort(key=lambda entry: entry.timestamp)

    return log_entries


def get_list_of_new_entries(device_entries: list, file_entries: list) -> list:
    """
    Compares log entries from the local logfile with the log entries from the device

    Args:
        device_entries (list): List of LogEntry Objects, fetched from the device
        file_entries (list): List of LogEntry Objects, fetched from the local logfile

    Raises:
        N/A

    Returns:
        new_entries (list): List of LogEntry objects from the device
        which are not yet present in the local logfile

    """
    new_entries = []
    # if there are no log entries in the local log file or it does not exist yet,
    # simply return the log entries from the device
    if not file_entries:
        return device_entries
    # if there are no log entries on the device, return empty list
    if not device_entries:
        return new_entries
    # otherwise, add the latest log entries from the device until
    # we reach a log entry already present in the local log file
    while device_entries[-1].timestamp > file_entries[-1].timestamp:
        new_entries.append(device_entries.pop())
    # sort by timestamp so the log entries are in the correct order (new entries last)
    new_entries.sort(key=lambda entry: entry.timestamp)

    return new_entries


def create_log_dir(log_dir="logs"):
    """
    Create log directory to store outputs.

    Args:
        log_dir (str): The name of the directory to be created.
            Default: "logs:

    Raises:
        N/A

    Returns:
        log_dir: The log directory for further usage.
    """
    # Create entry directory and/or check that it exists
    pl.Path(log_dir).mkdir(parents=True, exist_ok=True)
    return log_dir


def process_isp_logs(isp_address: str, isp_uname: str, isp_pword: str) -> list:
    """
    Function to join together multiple operations
    related to the Fritz ISP Router portion of the
    script.

    Args:
        isp_address (str): hostname / IP Address of the target FritzBox device
        isp_uname (str): Username to log in to the device
        isp_pword (str): Password to log in to the device

    Raises:
        N/A

    Returns:
        new_entries (list): List of LogEntry objects from the device
        which are not yet present in the local logfile.
        Can be used for further processing with a notifier.

    """
    # Create a logs directory to save the results into.
    log_dir = os.path.join(dirname, "..", "logs")
    output_dir = create_log_dir(log_dir=log_dir)
    log_file = f"{output_dir}/{isp_address}.log"
    # Initialise connection to Fritz ISP Router
    conn = FritzConnection(address=isp_address, user=isp_uname, password=isp_pword)
    # Read log entries from the local logfile
    file_entries = load_list_from_logfile(filepath=log_file)
    device_entries = get_list_from_device(conn=conn)
    # get the log entries which are present on the device
    # but not yet written to the local logfile
    new_entries = get_list_of_new_entries(
        file_entries=file_entries, device_entries=device_entries
    )
    # Append only the log entries which are not yet present to the local logfile
    append_list_to_logfile(log_entries=new_entries, filepath=log_file)
    # return the new log entries for the notifiers of choice
    return new_entries


# Main workflow


def main(stdout=True, gmail=False) -> None:
    """
    Main workflow of the script.

    NOTE: Gmail is used as the "notification" engine,
    but there is nothing stopping you using something else.

    Args:
        stdout: Boolean to toggle notification to stdout on/off
        gmail: Boolean to toggle gmail notification on/off
    """
    verify_env()
    # Assign environmental variables to variables for usage.
    isp_uname = environ.get("ISP_RTR_UNAME")
    isp_pword = environ.get("ISP_RTR_PWORD")
    isp_address = environ.get("ISP_RTR_ADDRESS")
    # Connect to Fritz ISP Router and process the logs
    new_entries = process_isp_logs(
        isp_address=isp_address, isp_uname=isp_uname, isp_pword=isp_pword
    )

    notifier = Notifier(isp_address=isp_address, new_entries=new_entries)
    if stdout:
        notifier = StdoutNotifier(isp_address=isp_address, new_entries=new_entries)
    if gmail:
        notifier = GmailNotifier(
            isp_address=isp_address,
            new_entries=new_entries,
            cred_dir=pl.Path.cwd().joinpath(dirname, "..", "creds"),
        )

    notifier.notify()


if __name__ == "__main__":
    main()
