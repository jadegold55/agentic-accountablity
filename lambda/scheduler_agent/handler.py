import logging

from graph import app
from langchain_core.messages import HumanMessage
import json
from shared.config import APP_TIME_ZONE, local_now
from shared.groq_client import generate_scheduled_message
from shared.db import (
    add_check_in,
    add_checkin_item,
    get_latest_checkin_by_event_id,
    update_checkin_status,
)
from shared.telegram import send_message as send_telegram_message
from state import SchedulerState
from tools import reset_invocation_state


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _build_reminder_message(event_title: str) -> str:
    return f"Reminder: {event_title} is starting now."


def _build_nudge_message(event_title: str) -> str:
    return f"Quick nudge: how did {event_title} go?"


def _render_scheduled_message(
    workflow_type: str, event_title: str, scheduled_for: str
) -> str:
    fallback = (
        _build_reminder_message(event_title)
        if workflow_type == "checkin"
        else _build_nudge_message(event_title)
    )
    try:
        candidate = generate_scheduled_message(
            workflow_type, event_title, scheduled_for
        ).strip()
        return candidate or fallback
    except Exception:
        logger.exception(
            "[scheduler_agent] failed to generate scheduled message for %s",
            workflow_type,
        )
        return fallback


def _should_skip_nudge(event: dict) -> bool:
    if event.get("type") != "nudge":
        return False

    calendar_event_id = event.get("calendar_event_id")
    if not calendar_event_id:
        return False

    checkins = get_latest_checkin_by_event_id(calendar_event_id) or []
    if not checkins:
        logger.info(
            "[scheduler_agent] no prior checkin found for nudge %s", calendar_event_id
        )
        return True

    latest_status = str(checkins[0].get("status", "")).lower()
    if latest_status != "sent":
        logger.info(
            "[scheduler_agent] skipping nudge for %s because latest status is %s",
            calendar_event_id,
            latest_status or "unknown",
        )
        return True

    return False


def _handle_scheduled_event(event: dict) -> None:
    workflow_type = event.get("type", "checkin")
    calendar_event_id = str(event["calendar_event_id"])
    event_title = str(event["event_title"])
    scheduled_for = str(event.get("scheduled_for", ""))

    if workflow_type == "checkin":
        result = add_check_in(
            {
                "calendar_event_id": calendar_event_id,
                "status": "sent",
            }
        )
        if not result:
            raise RuntimeError("failed to log scheduled check-in")
        add_checkin_item(
            {
                "checkin_id": str(result[0]["id"]),
                "event_title": event_title,
            }
        )
        send_telegram_message(
            _render_scheduled_message(workflow_type, event_title, scheduled_for)
        )
        return

    if workflow_type == "nudge":
        checkins = get_latest_checkin_by_event_id(calendar_event_id) or []
        if not checkins:
            raise RuntimeError("missing check-in for scheduled nudge")
        update_checkin_status(str(checkins[0]["id"]), "nudged")
        send_telegram_message(
            _render_scheduled_message(workflow_type, event_title, scheduled_for)
        )
        return

    raise RuntimeError(f"unsupported scheduled workflow type: {workflow_type}")


def lambda_handler(event, context):
    reset_invocation_state()
    if _should_skip_nudge(event):
        return {"statusCode": 200, "body": json.dumps("skipped")}

    if event.get("type") == "command":
        today = local_now().strftime("%Y-%m-%d")
        content = (
            f"Today is {today} in timezone {APP_TIME_ZONE}: " f"{event['message']}"
        )
        mode = "command"
    else:
        mode = "schedule"
    try:
        if mode == "command":
            initial_state: SchedulerState = {
                "messages": [HumanMessage(content=content)],
                "calendar_events": [],
                "mode": mode,
                "sms_sent": False,
            }
            app.invoke(initial_state)
        else:
            _handle_scheduled_event(event)
    except Exception as exc:
        logger.exception("scheduler_agent failed")
        error_message = str(exc).lower()
        if "rate_limit" in error_message:
            send_telegram_message(
                "I'm temporarily rate limited right now. "
                "Please try again in a few minutes."
            )
        elif mode == "command":
            send_telegram_message(
                "I couldn't safely find the event to update. "
                "Please try again with the exact event title."
            )
        else:
            send_telegram_message(
                "I couldn't complete the scheduled workflow right now."
            )
    return {"statusCode": 200, "body": json.dumps("ok")}
