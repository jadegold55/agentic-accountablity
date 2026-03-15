import importlib
from pathlib import Path
import sys
from types import SimpleNamespace


def load_scheduler_graph_module():
    scheduler_path = Path(__file__).resolve().parents[1] / "lambda" / "scheduler_agent"
    sys.path.insert(0, str(scheduler_path))
    importlib.invalidate_caches()
    return importlib.import_module("graph")


def test_route_after_tools_ends_after_command_message() -> None:
    graph = load_scheduler_graph_module()

    state = {
        "messages": [SimpleNamespace(name="send_message")],
        "mode": "command",
    }

    assert graph.route_after_tools(state) == graph.END


def test_route_after_tools_ends_after_schedule_logging() -> None:
    graph = load_scheduler_graph_module()

    state = {
        "messages": [SimpleNamespace(name="log_nudge")],
        "mode": "schedule",
    }

    assert graph.route_after_tools(state) == graph.END


def test_route_after_tools_continues_when_more_work_needed() -> None:
    graph = load_scheduler_graph_module()

    state = {
        "messages": [SimpleNamespace(name="update_calendar_event")],
        "mode": "command",
    }

    assert graph.route_after_tools(state) == "agent"
