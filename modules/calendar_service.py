"""
Google Calendar Service Module
Handles Google Calendar API authentication and event retrieval
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger('morning-briefing.calendar')

# Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


class CalendarService:
    """Google Calendar API service for retrieving events"""

    def __init__(self, credentials_path: str, token_path: str, timezone: str = 'America/Santo_Domingo'):
        """
        Initialize Calendar service

        Args:
            credentials_path: Path to Google OAuth credentials file
            token_path: Path to store/load OAuth token
            timezone: User's timezone
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.timezone = pytz.timezone(timezone)
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Google OAuth and build Calendar service"""
        creds = None

        # Load token if it exists
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                logger.info("Loaded existing OAuth token for Calendar")
            except Exception as e:
                logger.warning(f"Failed to load Calendar token: {e}")

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("Refreshed Calendar OAuth token")
                except Exception as e:
                    logger.error(f"Failed to refresh Calendar token: {e}")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        f"Please download credentials.json from Google Cloud Console"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("Completed OAuth flow for Calendar")

            # Save the token
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
                logger.info(f"Saved Calendar OAuth token to {self.token_path}")

        # Build the service
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar API service initialized successfully")
        except HttpError as error:
            logger.error(f"Failed to build Calendar service: {error}")
            raise

    def get_todays_events(
        self,
        calendar_ids: List[str] = ['primary'],
        include_all_day: bool = True,
        include_declined: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get today's calendar events

        Args:
            calendar_ids: List of calendar IDs to query
            include_all_day: Include all-day events
            include_declined: Include declined events

        Returns:
            List of event dictionaries with summary, start, end, location, attendees
        """
        try:
            # Get start and end of today in user's timezone
            now = datetime.now(self.timezone)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Convert to UTC for API
            time_min = start_of_day.astimezone(pytz.UTC).isoformat()
            time_max = end_of_day.astimezone(pytz.UTC).isoformat()

            all_events = []

            # Query each calendar
            for calendar_id in calendar_ids:
                try:
                    events_result = self.service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()

                    events = events_result.get('items', [])

                    for event in events:
                        # Check if declined
                        if not include_declined:
                            attendees = event.get('attendees', [])
                            user_declined = any(
                                att.get('self', False) and att.get('responseStatus') == 'declined'
                                for att in attendees
                            )
                            if user_declined:
                                continue

                        # Parse event
                        parsed_event = self._parse_event(event, include_all_day)
                        if parsed_event:
                            all_events.append(parsed_event)

                except HttpError as e:
                    logger.warning(f"Failed to get events from calendar {calendar_id}: {e}")
                    continue

            # Sort by start time
            all_events.sort(key=lambda x: x['start_datetime'])

            logger.info(f"Retrieved {len(all_events)} events for today")
            return all_events

        except HttpError as error:
            logger.error(f"Failed to retrieve calendar events: {error}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error retrieving events: {e}")
            return []

    def get_upcoming_events(
        self,
        days_forward: int = 7,
        calendar_ids: List[str] = ['primary'],
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming events for the next N days

        Args:
            days_forward: Number of days to look ahead
            calendar_ids: List of calendar IDs to query
            max_results: Maximum number of events per calendar

        Returns:
            List of event dictionaries
        """
        try:
            now = datetime.now(self.timezone)
            end_time = now + timedelta(days=days_forward)

            time_min = now.isoformat()
            time_max = end_time.isoformat()

            all_events = []

            for calendar_id in calendar_ids:
                try:
                    events_result = self.service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=max_results,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()

                    events = events_result.get('items', [])

                    for event in events:
                        parsed_event = self._parse_event(event)
                        if parsed_event:
                            all_events.append(parsed_event)

                except HttpError as e:
                    logger.warning(f"Failed to get upcoming events from {calendar_id}: {e}")
                    continue

            all_events.sort(key=lambda x: x['start_datetime'])

            logger.info(f"Retrieved {len(all_events)} upcoming events")
            return all_events

        except Exception as e:
            logger.error(f"Failed to retrieve upcoming events: {e}")
            return []

    def _parse_event(self, event: Dict[str, Any], include_all_day: bool = True) -> Optional[Dict[str, Any]]:
        """
        Parse a calendar event into a standardized format

        Args:
            event: Raw event from Calendar API
            include_all_day: Whether to include all-day events

        Returns:
            Parsed event dictionary or None if should be skipped
        """
        # Get start and end times
        start = event.get('start', {})
        end = event.get('end', {})

        # Check if all-day event
        is_all_day = 'date' in start

        if is_all_day and not include_all_day:
            return None

        # Parse datetime
        if is_all_day:
            start_str = start.get('date')
            end_str = end.get('date')
            start_dt = datetime.fromisoformat(start_str).replace(tzinfo=self.timezone)
            end_dt = datetime.fromisoformat(end_str).replace(tzinfo=self.timezone)
            time_str = 'All Day'
        else:
            start_str = start.get('dateTime')
            end_str = end.get('dateTime')
            start_dt = datetime.fromisoformat(start_str).astimezone(self.timezone)
            end_dt = datetime.fromisoformat(end_str).astimezone(self.timezone)
            time_str = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"

        # Get attendees
        attendees = event.get('attendees', [])
        attendee_emails = [att.get('email') for att in attendees if att.get('email')]

        # Get organizer
        organizer = event.get('organizer', {}).get('email', 'Unknown')

        return {
            'id': event.get('id'),
            'summary': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'location': event.get('location', ''),
            'start_datetime': start_dt,
            'end_datetime': end_dt,
            'time_str': time_str,
            'is_all_day': is_all_day,
            'attendees': attendee_emails,
            'organizer': organizer,
            'html_link': event.get('htmlLink', ''),
            'status': event.get('status', 'confirmed')
        }

    def detect_priority(self, event: Dict[str, Any], priority_keywords: Dict[str, List[str]]) -> str:
        """
        Detect event priority based on keywords

        Args:
            event: Parsed event dictionary
            priority_keywords: Dictionary of priority levels and their keywords

        Returns:
            Priority level ('high', 'medium', 'low', or 'normal')
        """
        summary_lower = event['summary'].lower()
        description_lower = event['description'].lower()
        combined_text = f"{summary_lower} {description_lower}"

        # Check for high priority keywords
        for keyword in priority_keywords.get('high', []):
            if keyword.lower() in combined_text:
                return 'high'

        # Check for medium priority keywords
        for keyword in priority_keywords.get('medium', []):
            if keyword.lower() in combined_text:
                return 'medium'

        # Check for low priority keywords
        for keyword in priority_keywords.get('low', []):
            if keyword.lower() in combined_text:
                return 'low'

        return 'normal'


def create_calendar_service(
    credentials_path: str,
    token_path: str,
    timezone: str = 'America/Santo_Domingo'
) -> CalendarService:
    """
    Create and return a Calendar service instance

    Args:
        credentials_path: Path to Google OAuth credentials file
        token_path: Path to store/load OAuth token
        timezone: User's timezone

    Returns:
        CalendarService instance
    """
    return CalendarService(credentials_path, token_path, timezone)
