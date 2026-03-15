import json
import re
from difflib import SequenceMatcher
from typing import Any, cast

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


Event = dict[str, Any]
_message_sent = False


def reset_invocation_state() -> None:
    global _message_sent
    _message_sent = False


def _event_start(event: Event) -> str:
    start = cast(dict[str, Any], event.get("start") or {})
    return start.get("dateTime") or start.get("date") or ""


def _event_end(event: Event) -> str:
    end = cast(dict[str, Any], event.get("end") or {})
    return end.get("dateTime") or end.get("date") or ""


def _serialize_events(events: list[Event]) -> str:
    simplified_events = [
        {
            "id": event.get("id", ""),
            "summary": event.get("summary", ""),
            "start": _event_start(event),
            "end": _event_end(event),
        }
        for event in events
    ]
    return json.dumps(simplified_events)


def _normalize_lookup(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _summary_tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if token}


def _summary_similarity(left: str, right: str) -> float:
    left_normalized = _normalize_lookup(left)
    right_normalized = _normalize_lookup(right)
    if not left_normalized or not right_normalized:
        return 0.0

    if left_normalized == right_normalized:
        return 1.0

    left_tokens = _summary_tokens(left)
    right_tokens = _summary_tokens(right)
    if left_tokens and right_tokens:
        token_overlap = len(left_tokens & right_tokens) / len(
            left_tokens | right_tokens
        )
        if token_overlap >= 0.5:
            return max(
                token_overlap,
                SequenceMatcher(None, left_normalized, right_normalized).ratio(),
            )

    return SequenceMatcher(None, left_normalized, right_normalized).ratio()


def _fuzzy_summary_matches(events: list[Event], summary: str) -> list[Event]:
    return [
        event
        for event in events
        if _summary_similarity(summary, str(event.get("summary", ""))) >= 0.6
    ]


def _resolve_event_id(date: str, event_id: str) -> tuple[str | None, list[Event]]:
    events = cast(list[Event], get_events(date) or [])
    if not events:
        return None, []

    for event in events:
        if event.get("id") == event_id:
            return event_id, events

    normalized_lookup = _normalize_lookup(event_id)
    summary_matches = [
        event
        for event in events
        if _normalize_lookup(event.get("summary", "")) == normalized_lookup
    ]
    if len(summary_matches) == 1:
        return summary_matches[0].get("id"), events

    fuzzy_matches = _fuzzy_summary_matches(events, event_id)
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0].get("id"), events

    return None, events


def _find_summary_matches(date: str, summary: str) -> list[Event]:
    events = cast(list[Event], get_events(date) or [])
    if not summary or not events:
        return []

    exact_matches = [
        event
        for event in events
        if _normalize_lookup(str(event.get("summary", "")))
        == _normalize_lookup(summary)
    ]
    if exact_matches:
        return exact_matches

    return _fuzzy_summary_matches(events, summary)


@tool
def send_message(message: str) -> str:
    """
    Sends a telegram message to the specified chat.
    """
    global _message_sent
    if _message_sent:
        return "A message has already been sent for this invocation."
    send_msg(message)
    _message_sent = True
    return "Message sent successfully."


@tool
def get_calendar_events_for_day(date: str) -> str:
    """
    Retrieves calendar events for a specific date.
    """
    events = cast(list[Event], get_events(date) or [])
    if not events:
        return "No events found for this date."
    return _serialize_events(events)


@tool
def add_calendar_event_for_day(date: str, event: dict) -> str:
    """
    Adds a calendar event for a specific date.

    The event dict must include summary plus start/end objects
    with dateTime and timeZone fields.
    """
    summary = str(event.get("summary", "")).strip()
    summary_matches = _find_summary_matches(date, summary)

    if len(summary_matches) == 1:
        matched_event_id = str(summary_matches[0].get("id", ""))
        update_event(date, matched_event_id, event)
        return (
            "Existing event matched by summary and updated successfully "
            f"with id {matched_event_id}."
        )

    if len(summary_matches) > 1:
        return (
            f"Multiple existing events match '{summary}' on {date}. "
            f"Use one of these exact events: {_serialize_events(summary_matches)}"
        )

    add_event(date, event)
    return "Event added successfully."


@tool
def update_calendar_event(date: str, event_id: str, updated_event: dict) -> str:
    """
    Updates a calendar event for a specific date.

    The updated_event dict must include summary plus start/end
    objects with dateTime and timeZone fields.
    """
    resolved_event_id, events = _resolve_event_id(date, event_id)
    if not resolved_event_id:
        if not events:
            return f"No events found on {date} to update."
        return (
            f"Could not find a unique event matching '{event_id}' on {date}. "
            f"Use one of these exact events: {_serialize_events(events)}"
        )

    update_event(date, resolved_event_id, updated_event)
    return f"Event updated successfully with id {resolved_event_id}."


@tool
def log_nudge(calendar_event_id: str) -> str:
    """
    Logs a nudge for an unanswered check-in.
    """
    checkins = cast(list[Event], get_checkin_by_event_id(calendar_event_id) or [])
    if not checkins:
        return "No checkin found for this event."
    update_checkin_status(str(checkins[0]["id"]), "nudged")
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
    result = cast(list[Event], add_check_in(checkin) or [])
    if not result:
        return "Failed to log check-in."
    checkin_id = str(result[0]["id"])
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
