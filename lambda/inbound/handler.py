import json
import logging
import re
from intent_router import classify_intent
import boto3
from shared.groq_client import interpret_completion_reply
from shared.db import (
    get_open_checkins,
    update_checkin_item_rating,
    update_checkin_status,
)
from shared.telegram import send_message as send_telegram_message

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _extract_rating(reply: str) -> int | None:
    stripped = reply.strip()
    if stripped.isdigit():
        rating = int(stripped)
        if 0 <= rating <= 5:
            return rating
    return None


def _confidence_is_usable(confidence: str) -> bool:
    return confidence.lower() in {"high", "medium"}


def _checkin_event_title(checkin: dict) -> str:
    items = checkin.get("checkin_items") or []
    if not items:
        return ""
    return str(items[0].get("event_title", "")).strip()


def _resolve_open_checkin(message: dict) -> tuple[dict | None, str]:
    open_checkins = get_open_checkins() or []
    if not open_checkins:
        return None, "none"

    reply_text = str(((message.get("reply_to_message") or {}).get("text")) or "")
    normalized_reply = _normalize_text(reply_text)
    if normalized_reply:
        matches = []
        for checkin in open_checkins:
            title = _checkin_event_title(checkin)
            normalized_title = _normalize_text(title)
            if normalized_title and normalized_title in normalized_reply:
                matches.append(checkin)
        if len(matches) == 1:
            return matches[0], "matched"
        if len(matches) > 1:
            return None, "ambiguous"

    if len(open_checkins) == 1:
        return open_checkins[0], "matched"

    return None, "ambiguous"


def lambda_handler(event, context):

    parse_event = json.loads(event["body"])
    message = parse_event["message"]

    reply = message["text"]
    logger.info(f"[inbound] received message: {reply}")
    matched_checkin, resolution = _resolve_open_checkin(message)
    rating = _extract_rating(reply)
    if rating is not None:
        if matched_checkin:
            checkin_items = matched_checkin.get("checkin_items") or []
            if checkin_items:
                checkin_item_id = checkin_items[0]["id"]
                update_checkin_item_rating(
                    checkin_item_id,
                    rating,
                    raw_reply_text=reply,
                    completion_summary=None,
                )
                update_checkin_status(
                    checkin_id=matched_checkin["id"], status="responded"
                )
        elif resolution == "ambiguous":
            send_telegram_message(
                "I have more than one follow-up waiting. Reply directly to the specific nudge with a number from 0 to 5."
            )
        else:
            send_telegram_message(
                "That reminder doesn't need a rating yet. I'll ask how it went in the follow-up nudge."
            )
        return {"statusCode": 200, "body": json.dumps("ok")}

    if matched_checkin:
        interpretation = interpret_completion_reply(
            reply, _checkin_event_title(matched_checkin)
        )
        intent = str(interpretation.get("intent", "")).strip().lower()
        confidence = str(interpretation.get("confidence", "low"))
        if intent == "log_completion" and _confidence_is_usable(confidence):
            inferred_rating = interpretation.get("rating")
            if isinstance(inferred_rating, int) and 0 <= inferred_rating <= 5:
                checkin_items = matched_checkin.get("checkin_items") or []
                if checkin_items:
                    checkin_item_id = checkin_items[0]["id"]
                    completion_summary = str(
                        interpretation.get("completion_summary", "")
                    ).strip()
                    update_checkin_item_rating(
                        checkin_item_id,
                        inferred_rating,
                        raw_reply_text=reply,
                        completion_summary=completion_summary or None,
                    )
                    update_checkin_status(
                        checkin_id=matched_checkin["id"], status="responded"
                    )
                    acknowledgment = str(
                        interpretation.get("acknowledgment", "")
                    ).strip()
                    if acknowledgment:
                        send_telegram_message(acknowledgment)
                    return {"statusCode": 200, "body": json.dumps("ok")}
        elif intent == "clarify_completion":
            clarifying_question = str(
                interpretation.get("clarifying_question", "")
            ).strip()
            if clarifying_question:
                send_telegram_message(clarifying_question)
                return {"statusCode": 200, "body": json.dumps("ok")}

    elif resolution == "ambiguous":
        send_telegram_message(
            "I have more than one follow-up waiting. Reply directly to the specific nudge so I know which one you mean."
        )
        return {"statusCode": 200, "body": json.dumps("ok")}

    intent = classify_intent(reply).strip(".")
    logger.info(f"[inbound] classified intent: '{intent}'")
    if intent == "command":
        logger.info(f"[inbound] invoking scheduler_agent with message: {reply}")
        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName="scheduler_agent",
            InvocationType="Event",
            Payload=json.dumps({"message": reply, "type": "command"}),
        )
        logger.info("[inbound] scheduler_agent invoked")
    elif intent == "rating":
        send_telegram_message(
            "That reminder doesn't need a rating yet. I'll ask how it went in the follow-up nudge."
        )
    elif intent == "question":
        pass

    return {"statusCode": 200, "body": json.dumps("ok")}
