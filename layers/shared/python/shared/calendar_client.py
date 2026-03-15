from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from datetime import datetime, time

from .config import (
    APP_TZINFO,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REFRESH_TOKEN,
)


def get_calendar_service():
    creds = Credentials.from_authorized_user_info(
        {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": GOOGLE_REFRESH_TOKEN,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )
    service = build("calendar", "v3", credentials=creds)
    return service


def get_events(date: str):
    service = get_calendar_service()
    local_date = datetime.fromisoformat(date).date()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=datetime.combine(local_date, time.min, APP_TZINFO).isoformat(),
            timeMax=datetime.combine(local_date, time.max, APP_TZINFO).isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    return events


def add_event(date: str, event: dict):
    service = get_calendar_service()
    event_result = service.events().insert(calendarId="primary", body=event).execute()
    return event_result


def update_event(date: str, event_id: str, updated_event: dict):
    service = get_calendar_service()
    event_result = (
        service.events()
        .update(calendarId="primary", eventId=event_id, body=updated_event)
        .execute()
    )
    return event_result
