import importlib
from pathlib import Path
import sys
from unittest.mock import patch


def load_intent_router_module():
    inbound_path = Path(__file__).resolve().parents[1] / "lambda" / "inbound"
    sys.path.insert(0, str(inbound_path))
    return importlib.import_module("intent_router")


def test_classify_intent_returns_rating_for_single_digit() -> None:
    intent_router = load_intent_router_module()

    assert intent_router.classify_intent("4") == "rating"


def test_classify_intent_returns_rating_for_multiple_digits() -> None:
    intent_router = load_intent_router_module()

    assert intent_router.classify_intent("5 3 0") == "rating"


def test_classify_intent_uses_groq_for_out_of_range_digit() -> None:
    intent_router = load_intent_router_module()

    with patch.object(
        intent_router, "classify_message", return_value="unknown"
    ) as mock_classify_message:
        assert intent_router.classify_intent("6") == "unknown"
        mock_classify_message.assert_called_once_with("6")


def test_classify_intent_uses_groq_for_text() -> None:
    intent_router = load_intent_router_module()

    with patch.object(
        intent_router, "classify_message", return_value="question"
    ) as mock_classify_message:
        assert intent_router.classify_intent("hello") == "question"
        mock_classify_message.assert_called_once_with("hello")


def test_classify_intent_uses_groq_for_empty_string() -> None:
    intent_router = load_intent_router_module()

    with patch.object(
        intent_router, "classify_message", return_value="question"
    ) as mock_classify_message:
        assert intent_router.classify_intent("") == "question"
        mock_classify_message.assert_called_once_with("")
