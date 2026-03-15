from datetime import datetime, timedelta, timezone
import json
import boto3
from calendar_reader import read_calendar_events
from shared.config import SCHEDULER_AGENT_ARN, SCHEDULER_ROLE_ARN


def cleanup_yesterday():
    client = boto3.client("scheduler")
    for prefix in ["checkin", "nudge"]:
        response = client.list_schedules(NamePrefix=prefix)
        schedules = response.get("Schedules", [])
        for schedule in schedules:
            client.delete_schedule(Name=schedule["Name"])


def setup_today():
    client = boto3.client("scheduler")
    events = read_calendar_events()
    for event in events:
        start_str = event["start"]["dateTime"]
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(event["end"]["dateTime"])
        duration_mins = (end_dt - start_dt).total_seconds() / 60
        utc = start_dt.astimezone(timezone.utc)
        schedule_expr = f"at({utc.strftime('%Y-%m-%dT%H:%M:%S')})"
        payload = {
            "type": "checkin",
            "calendar_event_id": event["id"],
            "event_title": event["summary"],
            "scheduled_for": start_str,
            "event_duration_mins": duration_mins,
        }

        client.create_schedule(
            Name=f"checkin-{event['id']}",
            ScheduleExpression=schedule_expr,
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": SCHEDULER_AGENT_ARN,
                "RoleArn": SCHEDULER_ROLE_ARN,
                "Input": json.dumps(payload),
            },
        )
        payload["type"] = "nudge"
        client.create_schedule(
            Name=f"nudge-{event['id']}",
            ScheduleExpression=(utc + timedelta(minutes=30)).strftime(
                "at(%Y-%m-%dT%H:%M:%S)"
            ),
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": SCHEDULER_AGENT_ARN,
                "RoleArn": SCHEDULER_ROLE_ARN,
                "Input": json.dumps(payload),
            },
        )
