from graph import app
from langchain_core.messages import HumanMessage
import json
from shared.config import APP_TIME_ZONE, local_now
from state import SchedulerState


def lambda_handler(event, context):
    if event.get("type") == "command":
        today = local_now().strftime("%Y-%m-%d")
        content = (
            f"Today is {today} in timezone {APP_TIME_ZONE}: " f"{event['message']}"
        )
    else:
        # build from calendar event fields
        content = (
            f"Calendar event '{event['event_title']}' scheduled for "
            f"{event['scheduled_for']} with duration "
            f"{event['event_duration_mins']} minutes."
        )
    initial_state: SchedulerState = {
        "messages": [HumanMessage(content=content)],
        "calendar_events": [],
        "sms_sent": False,
    }
    app.invoke(initial_state)
    return {"statusCode": 200, "body": json.dumps("ok")}
