import logging
from scraper import scraper

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        return scraper.lambda_handler(event, context)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": "Internal server error"
        }
