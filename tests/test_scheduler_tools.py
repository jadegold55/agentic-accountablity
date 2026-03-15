import importlib
from pathlib import Path
import sys
from unittest.mock import call
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
        patch.object(tools, "_refresh_event_schedules") as mock_refresh,
    ):
        mock_update_event.return_value = {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T11:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T11:30:00-04:00"},
        }
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
        mock_refresh.assert_called_once()
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
        patch.object(tools, "_refresh_event_schedules") as mock_refresh,
    ):
        mock_update_event.return_value = {"id": "abc123", **events[0]}
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
        mock_refresh.assert_called_once()
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
        patch.object(tools, "_refresh_event_schedules") as mock_refresh,
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
        mock_refresh.assert_not_called()
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
        patch.object(tools, "_refresh_event_schedules") as mock_refresh,
    ):
        mock_update_event.return_value = {"id": "abc123", **events[0]}
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
        mock_refresh.assert_called_once()
        assert result == (
            "Existing event matched by summary and updated successfully "
            "with id abc123."
        )


def test_add_calendar_event_creates_schedule_for_new_event() -> None:
    tools = load_scheduler_tools_module()

    with (
        patch.object(tools, "get_events", return_value=[]),
        patch.object(tools, "add_event") as mock_add_event,
        patch.object(tools, "_refresh_event_schedules") as mock_refresh,
    ):
        mock_add_event.return_value = {
            "id": "abc123",
            "summary": "Dentist appointment",
            "start": {"dateTime": "2026-03-15T14:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T14:30:00-04:00"},
        }

        result = tools.add_calendar_event_for_day.func(
            "2026-03-15",
            {
                "summary": "Dentist appointment",
                "start": {
                    "dateTime": "2026-03-15T14:00:00-04:00",
                    "timeZone": "America/New_York",
                },
                "end": {
                    "dateTime": "2026-03-15T14:30:00-04:00",
                    "timeZone": "America/New_York",
                },
            },
        )

        mock_add_event.assert_called_once()
        mock_refresh.assert_called_once()
        assert result == "Event added successfully."


def test_update_calendar_event_refreshes_event_schedules() -> None:
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
        patch.object(tools, "_refresh_event_schedules") as mock_refresh,
    ):
        mock_update_event.return_value = {
            "id": "abc123",
            "summary": "Meeting with Moira",
            "start": {"dateTime": "2026-03-15T11:00:00-04:00"},
            "end": {"dateTime": "2026-03-15T11:30:00-04:00"},
        }

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
        mock_refresh.assert_called_once()
        assert result == "Event updated successfully with id abc123."


def test_refresh_event_schedules_nudges_after_event_end() -> None:
    tools = load_scheduler_tools_module()

    event = {
        "id": "evt-123",
        "summary": "Deep work",
        "start": {"dateTime": "2026-03-15T09:00:00-04:00"},
        "end": {"dateTime": "2026-03-15T10:15:00-04:00"},
    }

    with (
        patch.object(
            tools,
            "SCHEDULER_AGENT_ARN",
            "arn:aws:lambda:region:acct:function:scheduler_agent",
        ),
        patch.object(tools, "SCHEDULER_ROLE_ARN", "arn:aws:iam::acct:role/scheduler"),
        patch.object(tools, "_upsert_schedule") as mock_upsert,
    ):
        tools._refresh_event_schedules(event)

        assert mock_upsert.call_args_list == [
            call(
                "checkin-evt-123",
                "at(2026-03-15T13:00:00)",
                {
                    "type": "checkin",
                    "calendar_event_id": "evt-123",
                    "event_title": "Deep work",
                    "scheduled_for": "2026-03-15T09:00:00-04:00",
                    "event_duration_mins": 75.0,
                },
            ),
            call(
                "nudge-evt-123",
                "at(2026-03-15T14:45:00)",
                {
                    "type": "nudge",
                    "calendar_event_id": "evt-123",
                    "event_title": "Deep work",
                    "scheduled_for": "2026-03-15T09:00:00-04:00",
                    "event_duration_mins": 75.0,
                },
            ),
        ]
