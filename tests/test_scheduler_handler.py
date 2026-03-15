import importlib
from pathlib import Path
import sys
from unittest.mock import patch


def load_scheduler_handler_module():
    scheduler_path = Path(__file__).resolve().parents[1] / "lambda" / "scheduler_agent"
    sys.path.insert(0, str(scheduler_path))
    importlib.invalidate_caches()
    return importlib.import_module("handler")


def test_lambda_handler_uses_local_date_in_command_prompt() -> None:
    handler = load_scheduler_handler_module()

    with (
        patch.object(handler, "local_now") as mock_local_now,
        patch.object(handler.app, "invoke") as mock_invoke,
    ):
        mock_local_now.return_value.strftime.return_value = "2026-03-14"

        handler.lambda_handler(
            {"type": "command", "message": "add a meeting tomorrow"}, None
        )

        state = mock_invoke.call_args.args[0]
        assert state["messages"][0].content == (
            "Today is 2026-03-14 in timezone America/New_York: "
            "add a meeting tomorrow"
        )
