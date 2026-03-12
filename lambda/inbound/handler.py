import urllib.parse
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    parsed_event = urllib.parse.parse_qs(event["body"])
    num = parsed_event["From"]
    reply = parsed_event["Body"]
    logger.info(f"[inbound] received message from {num}: {reply}")
    ratings = [int(r) for r in reply[0].split()]

    logger.info(f"[inbound] parsed ratings: {ratings}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/xml"},
        "body": '<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
    }
