import json
from datetime import datetime, timedelta
from typing import Any, cast

from langchain_core.messages import HumanMessage

from shared.db import get_checkin_items_by_date_range
from shared.telegram import send_message

from analyzer import analyze_week
from graph import app
from prompt_builder import build_summary_prompt


def lambda_handler(event, context):
    today = datetime.now()
    week_ago = today - timedelta(days=7)

    items = get_checkin_items_by_date_range(week_ago.isoformat(), today.isoformat())

    stats = analyze_week(items)

    if stats.get("per_task") is None:
        send_message("No check-in data this week!")
        return {"statusCode": 200, "body": json.dumps("ok")}

    prompt = build_summary_prompt(stats)

    initial_state = {
        "messages": [HumanMessage(content=prompt)],
        "weeklySummary": stats,
    }
    app.invoke(initial_state)

    return {"statusCode": 200, "body": json.dumps("ok")}
