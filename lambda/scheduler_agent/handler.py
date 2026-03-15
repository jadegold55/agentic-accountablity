import logging

from graph import app
from langchain_core.messages import HumanMessage
import json
from shared.config import APP_TIME_ZONE, local_now
from shared.db import get_latest_checkin_by_event_id
from shared.telegram import send_message as send_telegram_message
from state import SchedulerState
from tools import reset_invocation_state


logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
        # build from calendar event fields
        content = (
            f"Scheduled workflow type '{event.get('type', 'checkin')}' for "
            f"calendar event '{event['event_title']}' scheduled for "
            f"{event['scheduled_for']} with duration "
            f"{event['event_duration_mins']} minutes."
        )
        mode = "schedule"
    initial_state: SchedulerState = {
        "messages": [HumanMessage(content=content)],
        "calendar_events": [],
        "mode": mode,
        "sms_sent": False,
    }
    try:
        app.invoke(initial_state)
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
