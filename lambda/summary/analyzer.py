from shared.db import get_checkin_items_by_date_range
from datetime import datetime


def analyze_week(checkin_items):

    if not checkin_items:
        return {"average_rating": None, "total_checkins": 0}
    pertask = {}
    for item in checkin_items:
        if item["rating"] is None:
            continue
        name = item["tasks"]["name"]
        pertask[name] = pertask.get(name, []) + [item["rating"]]

    pertask = average(pertask)

    perday = {}
    for item in checkin_items:
        if item["rating"] is None:
            continue
        date = item["checkins"]["sent_at"]
        tme = datetime.fromisoformat(date)
        day_name = tme.strftime("%A")
        perday[day_name] = perday.get(day_name, []) + [item["rating"]]

    perday = average(perday)

    return {"per_task": pertask, "per_day": perday}


def average(per):
    if not per:
        return None
    for date in per:
        ratings = per[date]
        per[date] = sum(ratings) / len(ratings)
    return per
