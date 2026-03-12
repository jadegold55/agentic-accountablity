from graph import app
from langchain_core.messages import HumanMessage


def lambda_handler(event, context):
    if event.get("type") == "command":
        content = event["message"]
    else:
        # build from calendar event fields
        content = f"Calendar event '{event['event_title']}' scheduled for {event['scheduled_for']} with duration {event['event_duration_mins']} minutes."
    initial_state = {
        "messages": [HumanMessage(content=content)],
        "calendar_events": [],
        "sms_sent": False,
    }
    response = app.invoke(initial_state)
    return {"statusCode": 200, "body": response}
