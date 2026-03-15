import logging

from graph import app
from langchain_core.messages import HumanMessage
import json
from shared.config import APP_TIME_ZONE, local_now
from shared.telegram import send_message as send_telegram_message
from state import SchedulerState
from tools import reset_invocation_state


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    reset_invocation_state()
    if event.get("type") == "command":
        today = local_now().strftime("%Y-%m-%d")
        content = (
            f"Today is {today} in timezone {APP_TIME_ZONE}: " f"{event['message']}"
        )
        mode = "command"
    else:
        # build from calendar event fields
        content = (
            f"Calendar event '{event['event_title']}' scheduled for "
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
