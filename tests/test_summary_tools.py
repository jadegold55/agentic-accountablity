import importlib.util
from pathlib import Path
import sys
import tempfile


def load_summary_tools_module():
    summary_path = Path(__file__).resolve().parents[1] / "lambda" / "summary_agent"
    sys.path.insert(0, str(summary_path))
    module_path = summary_path / "tools.py"
    spec = importlib.util.spec_from_file_location(
        "summary_tools_under_test", module_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_summary_tools_use_headless_matplotlib_backend() -> None:
    tools = load_summary_tools_module()

    plt = tools._get_pyplot()

    assert plt.get_backend().lower() == "agg"


def test_send_photo_passes_through_exact_path() -> None:
    tools = load_summary_tools_module()

    chart_path = Path(tempfile.gettempdir()) / "bar_Task Completion Rates.png"
    chart_path.write_bytes(b"fake-image")

    from unittest.mock import patch

    with patch.object(tools, "telegram_send_photo") as mock_send:
        result = tools.send_photo(str(chart_path))

        mock_send.assert_called_once_with(str(chart_path), None)
        assert result == str(chart_path)

    chart_path.unlink(missing_ok=True)


def test_build_heat_map_inputs_returns_none_for_insufficient_data() -> None:
    tools = load_summary_tools_module()

    result = tools.build_heat_map_inputs(
        [
            {
                "event_title": "Code sesh",
                "rating": 4,
                "checkins": {"sent_at": "2026-03-10T14:00:00+00:00"},
            }
        ]
    )

    assert result is None


def test_build_heat_map_inputs_returns_matrix_for_multiple_tasks_and_days() -> None:
    tools = load_summary_tools_module()

    result = tools.build_heat_map_inputs(
        [
            {
                "event_title": "Code sesh",
                "rating": 4,
                "checkins": {"sent_at": "2026-03-10T14:00:00+00:00"},
            },
            {
                "event_title": "Gym",
                "rating": 3,
                "checkins": {"sent_at": "2026-03-11T14:00:00+00:00"},
            },
        ]
    )

    assert result == {
        "tasks": ["Code sesh", "Gym"],
        "days": ["Tue", "Wed"],
        "ratings": [[4.0, 0.0], [0.0, 3.0]],
    }
