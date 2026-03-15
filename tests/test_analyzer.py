import importlib
from pathlib import Path
import sys
from unittest.mock import patch


def load_analyzer_module():
    summary_path = Path(__file__).resolve().parents[1] / "lambda" / "summary_agent"
    sys.path.insert(0, str(summary_path))
    importlib.invalidate_caches()
    return importlib.import_module("analyzer")


def test_analyze_week_json():
    analyzer = load_analyzer_module()

    mock_items = [
        {
            "id": "fake-id-1",
            "checkin_id": "fake-checkin-1",
            "event_title": "Math class",
            "rating": 4,
            "checkins": {"sent_at": "2026-03-10T14:00:00+00:00"},
        },
        {
            "id": "fake-id-2",
            "checkin_id": "fake-checkin-2",
            "event_title": "Gym",
            "rating": 3,
            "checkins": {"sent_at": "2026-03-11T10:00:00+00:00"},
        },
    ]

    result = analyzer.analyze_week(mock_items)
    assert result["per_task"]["Math class"] == 4
    assert result["per_task"]["Gym"] == 3
    assert result["per_day"]["Tuesday"] == 4
    assert result["per_day"]["Wednesday"] == 3


def test_multiple_ratings_for_same_task():
    analyzer = load_analyzer_module()
    mock_items = [
        {
            "id": "fake-id-1",
            "checkin_id": "fake-checkin-1",
            "event_title": "Math class",
            "rating": 4,
            "checkins": {"sent_at": "2026-03-10T14:00:00+00:00"},
        },
        {
            "id": "fake-id-1",
            "checkin_id": "fake-checkin-2",
            "event_title": "Math class",
            "rating": 2,
            "checkins": {"sent_at": "2026-03-11T10:00:00+00:00"},
        },
    ]

    result = analyzer.analyze_week(mock_items)
    assert result["per_task"]["Math class"] == 3


def test_analyze_week_with_no_ratings():
    analyzer = load_analyzer_module()
    mock_items = [
        {
            "id": "fake-id-1",
            "checkin_id": "fake-checkin-1",
            "event_title": "Math class",
            "rating": None,
            "checkins": {"sent_at": "2026-03-10T14:00:00+00:00"},
        },
        {
            "id": "fake-id-2",
            "checkin_id": "fake-checkin-2",
            "event_title": "Gym",
            "rating": None,
            "checkins": {"sent_at": "2026-03-11T10:00:00+00:00"},
        },
    ]

    result = analyzer.analyze_week(mock_items)
    assert result["per_task"] is None
    assert result["per_day"] is None


def test_analyze_week_with_no_list():
    analyzer = load_analyzer_module()
    mock_items = []

    result = analyzer.analyze_week(mock_items)
    assert result["total_checkins"] == 0
    assert result["average_rating"] is None
