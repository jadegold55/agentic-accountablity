import json
import logging
import re
from intent_router import classify_intent
import boto3
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
    intent = classify_intent(reply).strip(".")
    logger.info(f"[inbound] classified intent: '{intent}'")
    if intent == "rating":
        rating = _extract_rating(reply)
        if rating is None:
            send_telegram_message(
                "Send one rating from 0 to 5 so I can log it correctly."
            )
        else:
            matched_checkin, resolution = _resolve_open_checkin(message)
            if matched_checkin:
                checkin_items = matched_checkin.get("checkin_items") or []
                if checkin_items:
                    checkin_item_id = checkin_items[0]["id"]
                    update_checkin_item_rating(checkin_item_id, rating)
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

    elif intent == "command":
        logger.info(f"[inbound] invoking scheduler_agent with message: {reply}")
        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName="scheduler_agent",
            InvocationType="Event",
            Payload=json.dumps({"message": reply, "type": "command"}),
        )
        logger.info("[inbound] scheduler_agent invoked")
    elif intent == "question":
        pass

    return {"statusCode": 200, "body": json.dumps("ok")}
