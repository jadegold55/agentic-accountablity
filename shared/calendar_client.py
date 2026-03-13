from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from config import GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_SECRET, GOOGLE_CLIENT_ID


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
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=f"{date}T00:00:00Z",
            timeMax=f"{date}T23:59:59Z",
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
