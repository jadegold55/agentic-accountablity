from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class SchedulerState(TypedDict):
    calendar_data_day: list[dict]
    messages: Annotated[list, add_messages]
    sms_sent: bool
