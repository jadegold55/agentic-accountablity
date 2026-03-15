import importlib.util
from pathlib import Path
import sys
from unittest.mock import patch


def load_inbound_handler_module():
    inbound_path = Path(__file__).resolve().parents[1] / "lambda" / "inbound"
    sys.path.insert(0, str(inbound_path))
    module_path = inbound_path / "handler.py"
    spec = importlib.util.spec_from_file_location(
        "inbound_handler_under_test", module_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rating_updates_single_open_checkin_even_when_nudged() -> None:
    handler = load_inbound_handler_module()

    event = {"body": '{"message": {"text": "4"}}'}
    open_checkins = [
        {
            "id": "checkin-1",
            "status": "nudged",
            "checkin_items": [{"id": "item-1", "event_title": "Code sesh"}],
        }
    ]

    with (
        patch.object(handler, "classify_intent", return_value="rating"),
        patch.object(handler, "get_open_checkins", return_value=open_checkins),
        patch.object(handler, "update_checkin_item_rating") as mock_update_rating,
        patch.object(handler, "update_checkin_status") as mock_update_status,
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        handler.lambda_handler(event, None)

        mock_update_rating.assert_called_once_with(
            "item-1",
            4,
            raw_reply_text="4",
            completion_summary=None,
        )
        mock_update_status.assert_called_once_with(
            checkin_id="checkin-1", status="responded"
        )
        mock_send.assert_not_called()


def test_natural_completion_reply_updates_single_nudged_checkin() -> None:
    handler = load_inbound_handler_module()

    event = {"body": '{"message": {"text": "I got through most of it"}}'}
    open_checkins = [
        {
            "id": "checkin-1",
            "status": "nudged",
            "checkin_items": [{"id": "item-1", "event_title": "Code sesh"}],
        }
    ]

    with (
        patch.object(handler, "get_open_checkins", return_value=open_checkins),
        patch.object(
            handler,
            "interpret_completion_reply",
            return_value={
                "intent": "log_completion",
                "rating": 4,
                "confidence": "high",
                "completion_summary": "User completed most of it.",
                "clarifying_question": "",
                "acknowledgment": "Nice. Sounds like Code sesh was mostly done.",
            },
        ) as mock_interpret,
        patch.object(handler, "classify_intent") as mock_classify_intent,
        patch.object(handler, "update_checkin_item_rating") as mock_update_rating,
        patch.object(handler, "update_checkin_status") as mock_update_status,
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        handler.lambda_handler(event, None)

        mock_interpret.assert_called_once_with("I got through most of it", "Code sesh")
        mock_update_rating.assert_called_once_with(
            "item-1",
            4,
            raw_reply_text="I got through most of it",
            completion_summary="User completed most of it.",
        )
        mock_update_status.assert_called_once_with(
            checkin_id="checkin-1", status="responded"
        )
        mock_send.assert_called_once_with(
            "Nice. Sounds like Code sesh was mostly done."
        )
        mock_classify_intent.assert_not_called()


def test_natural_completion_reply_can_ask_for_clarification() -> None:
    handler = load_inbound_handler_module()

    event = {"body": '{"message": {"text": "kind of"}}'}
    open_checkins = [
        {
            "id": "checkin-1",
            "status": "nudged",
            "checkin_items": [{"id": "item-1", "event_title": "Code sesh"}],
        }
    ]

    with (
        patch.object(handler, "get_open_checkins", return_value=open_checkins),
        patch.object(
            handler,
            "interpret_completion_reply",
            return_value={
                "intent": "clarify_completion",
                "rating": None,
                "confidence": "low",
                "completion_summary": "",
                "clarifying_question": "Would you say you got a little done or most of it done?",
                "acknowledgment": "",
            },
        ),
        patch.object(handler, "classify_intent") as mock_classify_intent,
        patch.object(handler, "update_checkin_item_rating") as mock_update_rating,
        patch.object(handler, "update_checkin_status") as mock_update_status,
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        handler.lambda_handler(event, None)

        mock_update_rating.assert_not_called()
        mock_update_status.assert_not_called()
        mock_send.assert_called_once_with(
            "Would you say you got a little done or most of it done?"
        )
        mock_classify_intent.assert_not_called()


def test_non_completion_reply_falls_back_to_command_handling() -> None:
    handler = load_inbound_handler_module()

    event = {"body": '{"message": {"text": "move tomorrow to 4"}}'}
    open_checkins = [
        {
            "id": "checkin-1",
            "status": "nudged",
            "checkin_items": [{"id": "item-1", "event_title": "Code sesh"}],
        }
    ]

    with (
        patch.object(handler, "get_open_checkins", return_value=open_checkins),
        patch.object(
            handler,
            "interpret_completion_reply",
            return_value={
                "intent": "not_completion",
                "rating": None,
                "confidence": "low",
                "completion_summary": "",
                "clarifying_question": "",
                "acknowledgment": "",
            },
        ),
        patch.object(
            handler, "classify_intent", return_value="command"
        ) as mock_classify_intent,
        patch.object(handler, "boto3") as mock_boto3,
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        mock_lambda = mock_boto3.client.return_value

        handler.lambda_handler(event, None)

        mock_classify_intent.assert_called_once_with("move tomorrow to 4")
        mock_lambda.invoke.assert_called_once()
        mock_send.assert_not_called()


def test_rating_does_not_attach_to_initial_reminder() -> None:
    handler = load_inbound_handler_module()

    event = {"body": '{"message": {"text": "4"}}'}

    with (
        patch.object(handler, "classify_intent", return_value="rating"),
        patch.object(handler, "get_open_checkins", return_value=[]),
        patch.object(handler, "update_checkin_item_rating") as mock_update_rating,
        patch.object(handler, "update_checkin_status") as mock_update_status,
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        handler.lambda_handler(event, None)

        mock_update_rating.assert_not_called()
        mock_update_status.assert_not_called()
        mock_send.assert_called_once_with(
            "That reminder doesn't need a rating yet. I'll ask how it went in the follow-up nudge."
        )


def test_rating_uses_replied_message_to_choose_checkin() -> None:
    handler = load_inbound_handler_module()

    event = {
        "body": (
            '{"message": {"text": "5", '
            '"reply_to_message": {"text": "Quick nudge: how did Code sesh go?"}}}'
        )
    }
    open_checkins = [
        {
            "id": "checkin-1",
            "status": "nudged",
            "checkin_items": [{"id": "item-1", "event_title": "Code sesh"}],
        },
        {
            "id": "checkin-2",
            "status": "sent",
            "checkin_items": [{"id": "item-2", "event_title": "Gym"}],
        },
    ]

    with (
        patch.object(handler, "classify_intent", return_value="rating"),
        patch.object(handler, "get_open_checkins", return_value=open_checkins),
        patch.object(handler, "update_checkin_item_rating") as mock_update_rating,
        patch.object(handler, "update_checkin_status") as mock_update_status,
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        handler.lambda_handler(event, None)

        mock_update_rating.assert_called_once_with(
            "item-1",
            5,
            raw_reply_text="5",
            completion_summary=None,
        )
        mock_update_status.assert_called_once_with(
            checkin_id="checkin-1", status="responded"
        )
        mock_send.assert_not_called()


def test_rating_does_not_guess_when_multiple_open_checkins_exist() -> None:
    handler = load_inbound_handler_module()

    event = {"body": '{"message": {"text": "3"}}'}
    open_checkins = [
        {
            "id": "checkin-1",
            "status": "nudged",
            "checkin_items": [{"id": "item-1", "event_title": "Code sesh"}],
        },
        {
            "id": "checkin-2",
            "status": "sent",
            "checkin_items": [{"id": "item-2", "event_title": "Gym"}],
        },
    ]

    with (
        patch.object(handler, "classify_intent", return_value="rating"),
        patch.object(handler, "get_open_checkins", return_value=open_checkins),
        patch.object(handler, "update_checkin_item_rating") as mock_update_rating,
        patch.object(handler, "update_checkin_status") as mock_update_status,
        patch.object(handler, "send_telegram_message") as mock_send,
    ):
        handler.lambda_handler(event, None)

        mock_update_rating.assert_not_called()
        mock_update_status.assert_not_called()
        mock_send.assert_called_once_with(
            "I have more than one follow-up waiting. Reply directly to the specific nudge with a number from 0 to 5."
        )
