"""
Gmail Service Module
Handles Gmail API authentication, email sending, and reading
"""

import os
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger('morning-briefing.gmail')

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly'
]


class GmailService:
    """Gmail API service for sending and reading emails"""

    def __init__(self, credentials_path: str, token_path: str):
        """
        Initialize Gmail service

        Args:
            credentials_path: Path to Google OAuth credentials file
            token_path: Path to store/load OAuth token
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google OAuth and build Gmail service"""
        creds = None

        # Load token if it exists
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                logger.info("Loaded existing OAuth token")
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed OAuth token")
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        f"Please download credentials.json from Google Cloud Console:\n"
                        f"1. Go to https://console.cloud.google.com\n"
                        f"2. Enable Gmail API\n"
                        f"3. Create OAuth 2.0 credentials (Desktop app)\n"
                        f"4. Download and save as credentials.json"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Completed OAuth flow, obtained new token")

            # Save the token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
                logger.info(f"Saved OAuth token to {self.token_path}")

        # Build the service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            logger.info("Gmail API service initialized successfully")
        except HttpError as error:
            logger.error(f"Failed to build Gmail service: {error}")
            raise

    def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_plain: Optional[str] = None
    ) -> bool:
        """
        Send an email via Gmail API

        Args:
            to: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_plain: Plain text body (optional, for fallback)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to
            message['subject'] = subject

            # Add plain text version if provided
            if body_plain:
                part_plain = MIMEText(body_plain, 'plain')
                message.attach(part_plain)

            # Add HTML version
            part_html = MIMEText(body_html, 'html')
            message.attach(part_html)

            # Encode message
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            send_message = {'raw': raw}
            result = self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()

            logger.info(f"Email sent successfully to {to}. Message ID: {result['id']}")
            return True

        except HttpError as error:
            logger.error(f"Failed to send email: {error}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            return False

    def get_recent_emails(
        self,
        days_back: int = 1,
        max_results: int = 10,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent emails matching criteria

        Args:
            days_back: How many days back to search
            max_results: Maximum number of results
            query: Gmail search query (e.g., "to:me is:unread")

        Returns:
            List of email dictionaries with id, subject, from, snippet, date
        """
        try:
            # Calculate date for query
            since_date = datetime.now() - timedelta(days=days_back)
            date_str = since_date.strftime('%Y/%m/%d')

            # Build query
            if query:
                search_query = f"{query} after:{date_str}"
            else:
                search_query = f"after:{date_str}"

            # Get messages
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])

            if not messages:
                logger.info("No recent emails found")
                return []

            # Get full message details
            emails = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()

                    headers = {h['name']: h['value'] for h in message['payload']['headers']}

                    emails.append({
                        'id': message['id'],
                        'subject': headers.get('Subject', 'No Subject'),
                        'from': headers.get('From', 'Unknown'),
                        'date': headers.get('Date', ''),
                        'snippet': message.get('snippet', '')
                    })
                except HttpError as e:
                    logger.warning(f"Failed to get message {msg['id']}: {e}")
                    continue

            logger.info(f"Retrieved {len(emails)} recent emails")
            return emails

        except HttpError as error:
            logger.error(f"Failed to retrieve emails: {error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving emails: {e}")
            return []

    def get_emails_with_keywords(
        self,
        keywords: List[str],
        days_back: int = 1,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get emails containing specific keywords

        Args:
            keywords: List of keywords to search for
            days_back: How many days back to search
            max_results: Maximum number of results

        Returns:
            List of email dictionaries
        """
        # Build query with keywords
        keyword_query = ' OR '.join([f'"{keyword}"' for keyword in keywords])
        query = f"({keyword_query})"

        return self.get_recent_emails(
            days_back=days_back,
            max_results=max_results,
            query=query
        )

    def get_unread_mentions(self, days_back: int = 1, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get unread emails where user is mentioned or in TO field

        Args:
            days_back: How many days back to search
            max_results: Maximum number of results

        Returns:
            List of email dictionaries
        """
        query = "to:me is:unread"
        return self.get_recent_emails(
            days_back=days_back,
            max_results=max_results,
            query=query
        )


def create_gmail_service(credentials_path: str, token_path: str) -> GmailService:
    """
    Create and return a Gmail service instance

    Args:
        credentials_path: Path to Google OAuth credentials file
        token_path: Path to store/load OAuth token

    Returns:
        GmailService instance
    """
    return GmailService(credentials_path, token_path)
