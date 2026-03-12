import logging
import json


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    cal_id = event["calendar_event_id"]
    event_title = event["event_title"]
    scheduled_for = event["scheduled_for"]
    event_duration_mins = event["event_duration_mins"]

    logger.info(
        f"[scheduler] time block for event {event_title} scheduled for {scheduled_for} with duration {event_duration_mins} minutes"
    )

    data = {
        "calendar_event_id": cal_id,
        "event_title": event_title,
        "scheduled_for": scheduled_for,
        "event_duration_mins": event_duration_mins,
    }

    logger.info(f"Returning data: {data}")

    return {"statusCode": 200, "body": json.dumps(data)}
