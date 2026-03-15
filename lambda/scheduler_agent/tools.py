from operator import add
from os import link

from langchain_core.tools import tool
from shared.db import (
    add_checkin_item,
    get_active_tasks,
    add_check_in,
    get_checkin_by_event_id,
    update_checkin_status,
)
from shared.telegram import send_message as send_msg
from shared.calendar_client import add_event, get_events, update_event


@tool
def send_message(message: str) -> str:
    """
    Sends a telegram message to the specified chat.
    """
    send_msg(message)
    return "Message sent successfully."


@tool
def get_calendar_events_for_day(date: str) -> str:
    """
    Retrieves calendar events for a specific date.
    """
    events = get_events(date)
    if not events:
        return "No events found for this date."
    return str(events)


@tool
def add_calendar_event_for_day(date: str, event: dict) -> str:
    """
    Adds a calendar event for a specific date. The event dict must include:
    summary (str), start (dict with dateTime and timeZone), end (dict with dateTime and timeZone).
    Example: {"summary": "Gym", "start": {"dateTime": "2026-03-14T07:00:00", "timeZone": "America/New_York"}, "end": {"dateTime": "2026-03-14T08:00:00", "timeZone": "America/New_York"}}
    """
    add_event(date, event)
    return "Event added successfully."


@tool
def update_calendar_event(date: str, event_id: str, updated_event: dict) -> str:
    """
    Updates a calendar event for a specific date. The updated_event dict must include:
    summary (str), start (dict with dateTime and timeZone), end (dict with dateTime and timeZone).
    Example: {"summary": "Gym", "start": {"dateTime": "2026-03-14T07:00:00", "timeZone": "America/New_York"}, "end": {"dateTime": "2026-03-14T08:00:00", "timeZone": "America/New_York"}}
    """
    update_event(date, event_id, updated_event)
    return "Event updated successfully."


@tool
def log_nudge(calendar_event_id: str) -> str:
    """
    Logs a nudge for an unanswered check-in.
    """
    checkin = get_checkin_by_event_id(calendar_event_id)
    if not checkin:
        return "No checkin found for this event."
    update_checkin_status(checkin[0]["id"], "nudged")
    return "Nudge logged successfully."


@tool
def log_check_in(calendar_event_id: str, event_title: str) -> str:
    """
    Logs a check-in for a calendar event.
    """
    checkin = {
        "calendar_event_id": calendar_event_id,
        "status": "sent",
    }
    result = add_check_in(checkin)
    checkin_id = result[0]["id"]
    linkitem = {
        "checkin_id": checkin_id,
        "event_title": event_title,
    }
    add_checkin_item(linkitem)
    return "Check-in logged successfully."


@tool
def get_tasks() -> str:
    """
    Retrieves a list of tasks for the user.
    """
    tasks = get_active_tasks()
    if not tasks:
        return "No active tasks found."
    return str(tasks)


tools = [
    send_message,
    get_calendar_events_for_day,
    add_calendar_event_for_day,
    update_calendar_event,
    log_nudge,
    log_check_in,
    get_tasks,
]
