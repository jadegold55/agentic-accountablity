from shared.calendar_client import get_events
from shared.config import local_now


def read_calendar_events():
    today = local_now()
    yymmdd = today.strftime("%Y-%m-%d")

    events = get_events(yymmdd)
    return events
