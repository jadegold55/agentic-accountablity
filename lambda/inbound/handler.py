import json
import logging
from intent_router import classify_intent
import boto3
from shared.db import update_checkin_item_rating

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    parse_event = json.loads(event["body"])

    reply = parse_event["message"]["text"]
    logger.info(f"[inbound] received message: {reply}")
    intent = classify_intent(reply)
    if intent == "rating":
        #----TODO-----
        #ratings = [int(r) for r in reply.split() if r.isdigit()]
        # Store the ratings in the database
        #update_checkin_item_rating(ratings)

    elif intent == "command":
        lambda_client = boto3.client("lambda")
        lambda_client.invoke(
            FunctionName="scheduler_agent",
            InvocationType="Event",
            Payload=json.dumps({"message": reply, "type": "command"}),
        )
    elif intent == "question":
        pass

    return {
    "statusCode": 200,
    "body": json.dumps("ok")
    }
