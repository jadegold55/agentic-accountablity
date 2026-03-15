import importlib.util
from datetime import datetime
from pathlib import Path
import sys
from unittest.mock import patch


def load_summary_handler_module():
    summary_path = (
        Path(__file__).resolve().parents[1] / "lambda" / "summary_agent"
    )
    sys.path.insert(0, str(summary_path))
    for module_name in ["handler", "tools", "analyzer", "prompt_builder"]:
        sys.modules.pop(module_name, None)
    module_path = summary_path / "handler.py"
    spec = importlib.util.spec_from_file_location(
        "summary_handler_under_test", module_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_summary_handler_generates_bar_chart_and_summary_text() -> None:
    handler = load_summary_handler_module()
    fixed_now = datetime(2026, 3, 15, 12, 0, 0)

    stats = {
        "per_task": {"Code sesh": 4.0},
        "per_day": {"Mon": 4.0},
        "completion_notes": [],
    }

    with (
        patch.object(handler, "datetime") as mock_datetime,
        patch.object(
            handler,
            "get_checkin_items_by_date_range",
            return_value=[
                {
                    "rating": 4,
                    "event_title": "Code sesh",
                    "checkins": {"sent_at": "2026-03-10T14:00:00+00:00"},
                }
            ],
        ),
        patch.object(handler, "analyze_week", return_value=stats),
        patch.object(
            handler,
            "generate_bar_chart",
            return_value="/tmp/bar_Task Completion Rates.png",
        ) as mock_bar,
        patch.object(handler, "build_heat_map_inputs", return_value=None),
        patch.object(handler, "send_photo") as mock_send_photo,
        patch.object(
            handler,
            "generate_weekly_summary",
            return_value="Solid week overall.",
        ) as mock_summary,
        patch.object(
            handler, "add_weekly_summary", return_value=[{"id": "sum-1"}]
        ) as mock_add_summary,
        patch.object(handler, "send_message") as mock_send_message,
    ):
        mock_datetime.now.return_value = fixed_now
        result = handler.lambda_handler({}, None)

        mock_bar.assert_called_once_with(
            ["Code sesh"],
            [4.0],
            "Task Completion Rates",
        )
        mock_send_photo.assert_called_once_with(
            "/tmp/bar_Task Completion Rates.png", "Average completion by task"
        )
        mock_summary.assert_called_once()
        mock_add_summary.assert_called_once_with(
            "2026-03-08T12:00:00",
            stats,
            "Solid week overall.",
        )
        mock_send_message.assert_called_once_with("Solid week overall.")
        assert result == {"statusCode": 200, "body": '"ok"'}


def test_summary_handler_generates_heatmap_when_inputs_available() -> None:
    handler = load_summary_handler_module()
    fixed_now = datetime(2026, 3, 15, 12, 0, 0)

    stats = {
        "per_task": {"Code sesh": 4.0, "Gym": 3.0},
        "per_day": {"Mon": 4.0, "Tue": 3.0},
        "completion_notes": [],
    }
    heat_map_inputs = {
        "tasks": ["Code sesh", "Gym"],
        "days": ["Mon", "Tue"],
        "ratings": [[4.0, 0.0], [0.0, 3.0]],
    }

    with (
        patch.object(handler, "datetime") as mock_datetime,
        patch.object(
            handler,
            "get_checkin_items_by_date_range",
            return_value=[],
        ),
        patch.object(handler, "analyze_week", return_value=stats),
        patch.object(
            handler,
            "generate_bar_chart",
            return_value="/tmp/bar_Task Completion Rates.png",
        ),
        patch.object(
            handler,
            "build_heat_map_inputs",
            return_value=heat_map_inputs,
        ),
        patch.object(
            handler,
            "generate_heat_map",
            return_value="/tmp/heatmap_Task Completion Heatmap.png",
        ) as mock_heat,
        patch.object(handler, "send_photo") as mock_send_photo,
        patch.object(
            handler,
            "generate_weekly_summary",
            return_value="Solid week overall.",
        ),
        patch.object(
            handler,
            "add_weekly_summary",
            return_value=[{"id": "sum-1"}],
        ),
        patch.object(handler, "send_message"),
    ):
        mock_datetime.now.return_value = fixed_now
        handler.lambda_handler({}, None)

        mock_heat.assert_called_once_with(
            ["Code sesh", "Gym"],
            ["Mon", "Tue"],
            [[4.0, 0.0], [0.0, 3.0]],
            "Task Completion Heatmap",
        )
        assert mock_send_photo.call_count == 2


def test_summary_handler_uses_fallback_summary_text_on_generation_error(
) -> None:
    handler = load_summary_handler_module()
    fixed_now = datetime(2026, 3, 15, 12, 0, 0)

    stats = {
        "per_task": {"Code sesh": 4.0},
        "per_day": {"Mon": 4.0},
        "completion_notes": [],
    }

    with (
        patch.object(handler, "datetime") as mock_datetime,
        patch.object(
            handler,
            "get_checkin_items_by_date_range",
            return_value=[],
        ),
        patch.object(handler, "analyze_week", return_value=stats),
        patch.object(
            handler,
            "generate_bar_chart",
            return_value="/tmp/bar_Task Completion Rates.png",
        ),
        patch.object(handler, "build_heat_map_inputs", return_value=None),
        patch.object(handler, "send_photo"),
        patch.object(
            handler,
            "generate_weekly_summary",
            side_effect=RuntimeError("rate_limit"),
        ),
        patch.object(
            handler, "add_weekly_summary", return_value=[{"id": "sum-1"}]
        ) as mock_add_summary,
        patch.object(handler, "send_message") as mock_send_message,
    ):
        mock_datetime.now.return_value = fixed_now
        handler.lambda_handler({}, None)

        mock_add_summary.assert_called_once_with(
            "2026-03-08T12:00:00",
            stats,
            (
                "You showed up this week and gave yourself real check-ins. "
                "Keep building on that momentum."
            ),
        )
        mock_send_message.assert_called_once_with(
            (
                "You showed up this week and gave yourself real check-ins. "
                "Keep building on that momentum."
            )
        )


def test_summary_handler_raises_when_weekly_summary_is_not_persisted() -> None:
    handler = load_summary_handler_module()
    fixed_now = datetime(2026, 3, 15, 12, 0, 0)

    stats = {
        "per_task": {"Code sesh": 4.0},
        "per_day": {"Mon": 4.0},
        "completion_notes": [],
    }

    with (
        patch.object(handler, "datetime") as mock_datetime,
        patch.object(
            handler,
            "get_checkin_items_by_date_range",
            return_value=[],
        ),
        patch.object(handler, "analyze_week", return_value=stats),
        patch.object(
            handler,
            "generate_bar_chart",
            return_value="/tmp/bar_Task Completion Rates.png",
        ),
        patch.object(handler, "build_heat_map_inputs", return_value=None),
        patch.object(handler, "send_photo"),
        patch.object(
            handler,
            "generate_weekly_summary",
            return_value="Solid week overall.",
        ),
        patch.object(handler, "add_weekly_summary", return_value=[]),
        patch.object(handler, "send_message") as mock_send_message,
    ):
        mock_datetime.now.return_value = fixed_now

        try:
            handler.lambda_handler({}, None)
        except RuntimeError as exc:
            assert str(exc) == "failed to persist weekly summary"
        else:
            raise AssertionError("expected summary persistence failure")

        mock_send_message.assert_not_called()
