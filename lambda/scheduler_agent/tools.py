from langchain_core.tools import tool
from shared.db import get_active_tasks, add_check_in
from shared.telegram import send_message as send_msg
from shared.calendar_client import add_event, get_events, update_event


@tool
def send_message(message: str) -> bool:
    """
    Sends a telegram message to the specified chat.
    """
    send_msg(message)
    return True


@tool
def get_calendar_events_for_day(date: str) -> list[dict]:
    """
    Retrieves calendar events for a specific date.
    """
    # Implement the logic to fetch calendar events here
    return get_events(date)


@tool
def add_calendar_event_for_day(date: str, event: dict) -> bool:
    """
    Adds a calendar event for a specific date.

    """
    add_event(date, event)
    # Implement the logic to add a calendar event here
    return True


@tool
def update_calendar_event(date: str, event_id: str, updated_event: dict) -> bool:
    """
    Updates a calendar event for a specific date.
    """
    # Implement the logic to update a calendar event here
    update_event(date, event_id, updated_event)
    return True


@tool
def log_nudge(user_id: str, message: str) -> bool:
    """
    Logs a nudge sent to a user.
    """
    # Implement the logic to log a nudge here
    return True


@tool
def log_check_in(user_id: str, timestamp: str) -> bool:
    """
    Logs a check-in for a user at a specific timestamp.
    """
    # add_check_in(user_id, timestamp)
    return True


@tool
def get_tasks():
    """
    Retrieves a list of tasks for the user.
    """
    return get_active_tasks()


tools = [
    send_message,
    get_calendar_events_for_day,
    add_calendar_event_for_day,
    update_calendar_event,
    log_nudge,
    log_check_in,
    get_tasks,
]
