import logging
import json

from schedule_manager import cleanup_yesterday, setup_today


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    cleanup_yesterday()
    setup_today()
    logger.info("Schedules updated successfully")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Schedules updated successfully"}),
    }
