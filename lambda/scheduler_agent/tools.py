from langchain_core.tools import tool


@tool
def send_sms(to: str, message: str) -> bool:
    """
    Sends an SMS message to the specified phone number.
    """
    # Implement the SMS sending logic here
    return True


@tool
def get_calendar_events_for_day(date: str) -> list[dict]:
    """
    Retrieves calendar events for a specific date.
    """
    # Implement the logic to fetch calendar events here
    return []


@tool
def add_calendar_event_for_day(date: str, event: dict) -> bool:
    """
    Adds a calendar event for a specific date.
    """
    # Implement the logic to add a calendar event here
    return True


@tool
def update_calendar_event(date: str, event_id: str, updated_event: dict) -> bool:
    """
    Updates a calendar event for a specific date.
    """
    # Implement the logic to update a calendar event here
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
    # Implement the logic to log a check-in here
    return True


@tool
def get_tasks():
    """
    Retrieves a list of tasks for the user.
    """
    # Implement the logic to fetch tasks here
    return []


tools = [
    send_sms,
    get_calendar_events_for_day,
    add_calendar_event_for_day,
    update_calendar_event,
    log_nudge,
    log_check_in,
    get_tasks,
]
