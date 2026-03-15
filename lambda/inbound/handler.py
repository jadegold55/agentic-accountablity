import json
import logging
from tabnanny import check
from intent_router import classify_intent
import boto3
from shared.db import (
    get_checkin_item_by_id,
    get_latest_unanswered_checkin,
    update_checkin_item_rating,
    update_checkin_status,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    parse_event = json.loads(event["body"])

    reply = parse_event["message"]["text"]
    logger.info(f"[inbound] received message: {reply}")
    intent = classify_intent(reply).strip(".")
    logger.info(f"[inbound] classified intent: '{intent}'")
    if intent == "rating":
        # ----TODO-----
        latest_checkin = get_latest_unanswered_checkin()
        if latest_checkin:
            checkin_items = get_checkin_item_by_id(latest_checkin[0]["id"])
            if checkin_items:
                checkin_item_id = checkin_items[0]["id"]
                update_checkin_item_rating(checkin_item_id, int(reply))
                update_checkin_status(
                    checkin_id=latest_checkin[0]["id"], status="responded"
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
