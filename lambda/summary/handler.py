import json
from datetime import datetime, timedelta
from shared.db import get_checkin_items_by_date_range
from shared.telegram import send_message
from shared.groq_client import classify_message
from groq import Groq
from shared.config import GROQ_API_KEY
from analyzer import analyze_week
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

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a supportive accountability coach for a college student.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    summary_text = response.choices[0].message.content
    send_message(summary_text)

    return {"statusCode": 200, "body": json.dumps("ok")}
