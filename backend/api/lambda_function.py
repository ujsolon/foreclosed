"""
AWS Lambda Function Handler for Property API
"""
import json
import logging
from main import route_request

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    AWS Lambda handler function
    
    Args:
        event: API Gateway event containing request details
        context: Lambda context object
        
    Returns:
        API Gateway response with statusCode, headers, and body
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Route the request to appropriate handler
        response = route_request(event)
        
        logger.info(f"Returning response with status: {response.get('statusCode')}")
        return response
        
    except Exception as e:
        logger.error(f"Unhandled exception in lambda_handler: {e}", exc_info=True)
        
        # Return generic error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "error": "Internal server error",
                "message": str(e)
            })
        }

# Made with Bob
