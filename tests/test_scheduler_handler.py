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
        assert state["mode"] == "command"


def test_lambda_handler_uses_schedule_mode_for_automated_events() -> None:
    handler = load_scheduler_handler_module()

    with (
        patch.object(handler, "add_check_in", return_value=[{"id": "chk-1"}]),
        patch.object(handler, "add_checkin_item") as mock_add_item,
        patch.object(
            handler,
            "generate_scheduled_message",
            return_value="Heads up, Standup is starting now.",
        ) as mock_generate,
        patch.object(handler, "send_telegram_message") as mock_send,
        patch.object(handler.app, "invoke") as mock_invoke,
    ):
        handler.lambda_handler(
            {
                "event_title": "Standup",
                "calendar_event_id": "evt-123",
                "scheduled_for": "2026-03-15T09:00:00-04:00",
                "event_duration_mins": 30,
            },
            None,
        )

        mock_invoke.assert_not_called()
        mock_add_item.assert_called_once_with(
            {"checkin_id": "chk-1", "event_title": "Standup"}
        )
        mock_generate.assert_called_once_with(
            "checkin", "Standup", "2026-03-15T09:00:00-04:00"
        )
        mock_send.assert_called_once_with("Heads up, Standup is starting now.")


def test_lambda_handler_skips_nudge_after_response() -> None:
    handler = load_scheduler_handler_module()

    with (
        patch.object(
            handler,
            "get_latest_checkin_by_event_id",
            return_value=[{"id": "chk1", "status": "responded"}],
        ),
        patch.object(handler.app, "invoke") as mock_invoke,
    ):
        result = handler.lambda_handler(
            {
                "type": "nudge",
                "calendar_event_id": "evt-123",
                "event_title": "Standup",
                "scheduled_for": "2026-03-15T09:00:00-04:00",
                "event_duration_mins": 30,
            },
            None,
        )

        mock_invoke.assert_not_called()
        assert result == {"statusCode": 200, "body": '"skipped"'}


def test_lambda_handler_runs_nudge_when_checkin_unanswered() -> None:
    handler = load_scheduler_handler_module()

    with (
        patch.object(
            handler,
            "get_latest_checkin_by_event_id",
            return_value=[{"id": "chk1", "status": "sent"}],
        ),
        patch.object(handler, "update_checkin_status") as mock_update_status,
        patch.object(
            handler,
            "generate_scheduled_message",
            return_value="How'd Standup go?",
        ) as mock_generate,
        patch.object(handler, "send_telegram_message") as mock_send,
        patch.object(handler.app, "invoke") as mock_invoke,
    ):
        handler.lambda_handler(
            {
                "type": "nudge",
                "calendar_event_id": "evt-123",
                "event_title": "Standup",
                "scheduled_for": "2026-03-15T09:00:00-04:00",
                "event_duration_mins": 30,
            },
            None,
        )

        mock_invoke.assert_not_called()
        mock_update_status.assert_called_once_with("chk1", "nudged")
        mock_generate.assert_called_once_with(
            "nudge", "Standup", "2026-03-15T09:00:00-04:00"
        )
        mock_send.assert_called_once_with("How'd Standup go?")


def test_lambda_handler_uses_fallback_message_when_generation_fails() -> None:
    handler = load_scheduler_handler_module()

    with (
        patch.object(handler, "add_check_in", return_value=[{"id": "chk-1"}]),
        patch.object(handler, "add_checkin_item"),
        patch.object(
            handler,
            "generate_scheduled_message",
            side_effect=RuntimeError("rate_limit"),
        ),
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        handler.lambda_handler(
            {
                "type": "checkin",
                "event_title": "Standup",
                "calendar_event_id": "evt-123",
                "scheduled_for": "2026-03-15T09:00:00-04:00",
                "event_duration_mins": 30,
            },
            None,
        )

        mock_send.assert_called_once_with("Reminder: Standup is starting now.")
