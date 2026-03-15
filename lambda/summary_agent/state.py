from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class SummaryState(TypedDict):
    weeklySummary: dict
    messages: Annotated[list[str], add_messages]
