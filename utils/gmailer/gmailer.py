import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
from email.mime.text import MIMEText
from apiclient import errors
import os

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

class GMailer:
    def __init__(self):
        self.service = build('gmail', 'v1', credentials=self.set_creds())


    def set_creds(self):
        creds = None
        if os.path.exists(f'{CURRENT_DIR}/token.pickle'):
            with open(f'{CURRENT_DIR}/token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                creds = (
                    InstalledAppFlow
                        .from_client_secrets_file(
                            f'{CURRENT_DIR}/credentials.json',
                            SCOPES,
                        )
                        .run_local_server(port=0)
                )
            # Save the credentials for the next run
            with open(f'{CURRENT_DIR}/token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds


    def create_message(self, sender, to, subject, message_text):
        """Create a message for an email.

        Args:
            sender: Email address of the sender.
            to: Email address of the receiver.
            subject: The subject of the email message.
            message_text: The text of the email message.

        Returns:
            An object containing a base64url encoded email object.
        """
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        return {
            'raw': (
                base64
                    .urlsafe_b64encode(message.as_string().encode())
                    .decode('ascii')
            )
        }


    def send_message(self, user_id, message):
        """Send an email message.

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
                self.service
                    .users()
                    .messages()
                    .send(userId=user_id, body=message)
                    .execute()
            )
            print(f"Message ID: {message['id']}")
            return message
        except errors.HttpError as error:
            print(f'An error occurred: {error}')
