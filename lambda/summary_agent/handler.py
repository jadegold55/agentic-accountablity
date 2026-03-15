import json
from datetime import datetime, timedelta
import logging

from shared.groq_client import generate_weekly_summary
from shared.db import add_weekly_summary, get_checkin_items_by_date_range
from shared.telegram import send_message

from analyzer import analyze_week
from prompt_builder import build_summary_prompt
import tools as summary_tools


logger = logging.getLogger()
logger.setLevel(logging.INFO)

build_heat_map_inputs = summary_tools.build_heat_map_inputs
generate_bar_chart = summary_tools.generate_bar_chart
generate_heat_map = summary_tools.generate_heat_map
send_photo = summary_tools.send_photo

FALLBACK_SUMMARY_TEXT = (
    "You showed up this week and gave yourself real check-ins. "
    "Keep building on that momentum."
)


def _persist_weekly_summary(
    week_start: datetime, stats: dict, summary_text: str
) -> None:
    result = add_weekly_summary(week_start.isoformat(), stats, summary_text)
    if not result:
        raise RuntimeError("failed to persist weekly summary")


def lambda_handler(event, context):
    today = datetime.now()
    week_ago = today - timedelta(days=7)

    items = get_checkin_items_by_date_range(
        week_ago.isoformat(),
        today.isoformat(),
    )

    stats = analyze_week(items)

    if stats.get("per_task") is None:
        send_message("No check-in data this week!")
        return {"statusCode": 200, "body": json.dumps("ok")}

    task_labels = list(stats["per_task"].keys())
    task_values = list(stats["per_task"].values())
    if task_labels and task_values:
        bar_chart_path = generate_bar_chart(
            task_labels,
            task_values,
            "Task Completion Rates",
        )
        send_photo(bar_chart_path, "Average completion by task")

    heat_map_inputs = build_heat_map_inputs(items)
    if heat_map_inputs:
        heat_map_path = generate_heat_map(
            heat_map_inputs["tasks"],
            heat_map_inputs["days"],
            heat_map_inputs["ratings"],
            "Task Completion Heatmap",
        )
        send_photo(heat_map_path, "Completion patterns across the week")

    prompt = build_summary_prompt(stats)

    try:
        summary_text = generate_weekly_summary(prompt).strip()
    except Exception:
        logger.exception("summary_agent failed to generate summary text")
        summary_text = FALLBACK_SUMMARY_TEXT

    _persist_weekly_summary(week_ago, stats, summary_text)

    if summary_text:
        send_message(summary_text)

    return {"statusCode": 200, "body": json.dumps("ok")}
