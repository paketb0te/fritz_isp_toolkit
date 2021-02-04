"""
Module containing notifiers for the fritz_isp_toolkit
"""

# Import modules
import base64
import os.path
import pickle  # nosec
import datetime
from email.mime import multipart, text
import apiclient
import classes
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class StdoutNotifier(classes.Notifier):  # pylint: disable=too-few-public-methods
    """
    Notifier printing new LogEntry objects to stdout.
    """

    def notify(self) -> None:
        """
        Print new LogEntry objects to stdout
        """
        if self.new_entries:
            print("-" * 80)
            print(f"{len(self.new_entries)} new log entries on {self.isp_address}:\n")
            for entry in self.new_entries:
                print(entry)
            print("-" * 80)
        else:
            print("-" * 80)
            print(f"Now new entries on {self.isp_address}.")
            print("-" * 80)


class GmailNotifier(classes.Notifier):
    """
    Notifier sending mail via gmail API
    """

    def __init__(self, isp_address: str, new_entries: list, cred_dir: str) -> None:
        super().__init__(isp_address, new_entries)
        self.cred_dir = cred_dir
        # Gmail API scopes
        # NOTE: If modifying these scopes, delete the file token.pickle
        # from within the CRED_DIR directory
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.send"
        ]  # Only need this scope to send email

    def authorise_gmail_service(self):
        """
        Authorise and establish connection
        to the Gmail service so that operations
        can be performed against the Gmail API.


        Args:
            N/A

        Raises:
            N/A

        Returns:
            service: An established object with
            access to the Gmail API

        """
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(os.path.join(self.cred_dir, "token.pickle")):
            with open(os.path.join(self.cred_dir, "token.pickle"), "rb") as token:
                creds = pickle.load(token)  # nosec
        # If there are no (valid) credentials available, let the user log in.
        # to generate more credentials.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.join(self.cred_dir, "credentials_home_automation.json"),
                    self.scopes,
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run into the self.cred_dir
            with open(os.path.join(self.cred_dir, "token.pickle"), "wb") as token:
                pickle.dump(creds, token)
        # Create the resource which will be used against the Gmail API
        service = build("gmail", "v1", credentials=creds)
        return service

    def create_message(self, recipient: str, subject: str, new_entries: list):
        """
        Send an email using the Gmail API with one or more attachments.

        Args:
            to: The to recipient of the email.
                Example: johndoe@gmail.com
            subject: The subject of the email.
            service: An established object with authorised access to the Gmail API
            for sending emails.
            message_text: The body of the message to be sent.

        Raises:
            N/A

        Returns:
            message: A message in the proper format, ready to be sent
            by the send_email function.
        """
        # Create the message string from LogEntry objects
        message_text = f"New log entries have been fetched from {self.isp_address}:\n\n"
        for new_entry in new_entries:
            message_text.append(new_entry)

        # Create an email message
        mime_message = multipart.MIMEMultipart()
        mime_message["to"] = recipient
        mime_message["subject"] = subject
        mime_message.attach(text.MIMEText(message_text, "plain"))

        # Format message dictionary, ready for sending
        message = {"raw": base64.urlsafe_b64encode(mime_message.as_bytes()).decode()}
        return message

    @staticmethod
    def send_message(service, user_id, message):
        """
        Send an email message.

        Args:
            service: Authorized Gmail API service instance.
            user_id: User's email address. The special value "me"
            can be used to indicate the authenticated user.
            message: Message to be sent.

        Returns:
            Sent Message.
        """
        try:
            message = (
                service.users().messages().send(userId=user_id, body=message).execute()
            )
            message_id = message["id"]
            print(f"Message Sent - Message ID: {message_id}")
            return message
        except apiclient.errors.HttpError as err:
            print(f"An error occurred: {err}")

    def notify(self) -> None:
        """
        Send new LogEntry objects via gmail API
        """
        # Authorise to the gmail service
        service = self.authorise_gmail_service()
        # Create email with attachment function
        message = self.create_message(
            recipient="danielfjteycheney@gmail.com",
            subject=f"ISP Log File Report - {datetime.datetime.now()}",
            new_entries=self.new_entries,
        )
        # Send the email
        self.send_message(service=service, user_id="me", message=message)
