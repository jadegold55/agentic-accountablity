import importlib
from pathlib import Path
import sys
from unittest.mock import patch


def load_scheduler_tools_module():
    scheduler_path = Path(__file__).resolve().parents[1] / "lambda" / "scheduler_agent"
    sys.path.insert(0, str(scheduler_path))
    importlib.invalidate_caches()
    return importlib.import_module("tools")


def test_update_calendar_event_resolves_summary_to_real_id() -> None:
    tools = load_scheduler_tools_module()

    events = [
        {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T10:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T10:30:00-04:00"},
        }
    ]

    with (
        patch.object(tools, "get_events", return_value=events),
        patch.object(tools, "update_event") as mock_update_event,
    ):
        result = tools.update_calendar_event.func(
            "2026-03-15",
            "meeting_with_moira",
            {
                "summary": "Meeting with Moira",
                "start": {
                    "dateTime": "2026-03-15T11:00:00-04:00",
                    "timeZone": "America/New_York",
                },
                "end": {
                    "dateTime": "2026-03-15T11:30:00-04:00",
                    "timeZone": "America/New_York",
                },
            },
        )

        mock_update_event.assert_called_once()
        assert mock_update_event.call_args.args[1] == "abc123"
        assert result == "Event updated successfully with id abc123."


def test_update_calendar_event_rejects_unknown_event() -> None:
    tools = load_scheduler_tools_module()

    events = [
        {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T10:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T10:30:00-04:00"},
        }
    ]

    with (
        patch.object(tools, "get_events", return_value=events),
        patch.object(tools, "update_event") as mock_update_event,
    ):
        result = tools.update_calendar_event.func(
            "2026-03-15",
            "not_a_real_event",
            {"summary": "Meeting with Moira"},
        )

        mock_update_event.assert_not_called()
        assert "Could not find a unique event matching 'not_a_real_event'" in result


def test_get_calendar_events_for_day_returns_json_ids() -> None:
    tools = load_scheduler_tools_module()

    events = [
        {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T10:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T10:30:00-04:00"},
        }
    ]

    with patch.object(tools, "get_events", return_value=events):
        result = tools.get_calendar_events_for_day.func("2026-03-15")

        assert '"id": "abc123"' in result
        assert '"summary": "Meeting with Moira"' in result


def test_send_message_only_sends_once_per_invocation() -> None:
    tools = load_scheduler_tools_module()

    tools.reset_invocation_state()

    with patch.object(tools, "send_msg") as mock_send_msg:
        first_result = tools.send_message.func("Updated successfully")
        second_result = tools.send_message.func("Updated successfully again")

        mock_send_msg.assert_called_once_with("Updated successfully")
        assert first_result == "Message sent successfully."
        assert second_result == "A message has already been sent for this invocation."


def test_add_calendar_event_updates_single_matching_summary() -> None:
    tools = load_scheduler_tools_module()

    events = [
        {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T10:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T10:30:00-04:00"},
        }
    ]

    with (
        patch.object(tools, "get_events", return_value=events),
        patch.object(tools, "update_event") as mock_update_event,
        patch.object(tools, "add_event") as mock_add_event,
    ):
        result = tools.add_calendar_event_for_day.func(
            "2026-03-15",
            {
                "summary": "Meeting with Moira",
                "start": {
                    "dateTime": "2026-03-15T11:00:00-04:00",
                    "timeZone": "America/New_York",
                },
                "end": {
                    "dateTime": "2026-03-15T11:30:00-04:00",
                    "timeZone": "America/New_York",
                },
            },
        )

        mock_update_event.assert_called_once()
        mock_add_event.assert_not_called()
        assert result == (
            "Existing event matched by summary and updated successfully "
            "with id abc123."
        )


def test_add_calendar_event_rejects_ambiguous_summary_matches() -> None:
    tools = load_scheduler_tools_module()

    events = [
        {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T10:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T10:30:00-04:00"},
        },
        {
            "id": "def456",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T14:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T14:30:00-04:00"},
        },
    ]

    with (
        patch.object(tools, "get_events", return_value=events),
        patch.object(tools, "update_event") as mock_update_event,
        patch.object(tools, "add_event") as mock_add_event,
    ):
        result = tools.add_calendar_event_for_day.func(
            "2026-03-15",
            {
                "summary": "Meeting with Moira",
                "start": {
                    "dateTime": "2026-03-15T11:00:00-04:00",
                    "timeZone": "America/New_York",
                },
                "end": {
                    "dateTime": "2026-03-15T11:30:00-04:00",
                    "timeZone": "America/New_York",
                },
            },
        )

        mock_update_event.assert_not_called()
        mock_add_event.assert_not_called()
        assert "Multiple existing events match 'Meeting with Moira'" in result


def test_add_calendar_event_updates_fuzzy_matching_summary() -> None:
    tools = load_scheduler_tools_module()

    events = [
        {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T10:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T10:30:00-04:00"},
        }
    ]

    with (
        patch.object(tools, "get_events", return_value=events),
        patch.object(tools, "update_event") as mock_update_event,
        patch.object(tools, "add_event") as mock_add_event,
    ):
        result = tools.add_calendar_event_for_day.func(
            "2026-03-15",
            {
                "summary": "Moira meeting",
                "start": {
                    "dateTime": "2026-03-15T11:00:00-04:00",
                    "timeZone": "America/New_York",
                },
                "end": {
                    "dateTime": "2026-03-15T11:30:00-04:00",
                    "timeZone": "America/New_York",
                },
            },
        )

        mock_update_event.assert_called_once()
        mock_add_event.assert_not_called()
        assert result == (
            "Existing event matched by summary and updated successfully "
            "with id abc123."
        )
