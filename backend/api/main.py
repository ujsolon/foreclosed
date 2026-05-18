"""
API Main Module - Handles property queries from DynamoDB
"""
import os
import json
import base64
from decimal import Decimal
from typing import Dict, Any, List, Optional
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
TABLE_NAME = os.environ.get("TABLE_NAME", "properties")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_PROFILE = os.environ.get("AWS_PROFILE", None)
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "*")

# Initialize DynamoDB with better error handling
try:
    if AWS_PROFILE:
        logger.info(f"Using AWS profile: {AWS_PROFILE}")
        session = boto3.Session(profile_name=AWS_PROFILE)
        dynamodb = session.resource("dynamodb", region_name=AWS_REGION)
    else:
        logger.info(f"Using default AWS credentials")
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    
    table = dynamodb.Table(TABLE_NAME)
    logger.info(f"Connected to DynamoDB table: {TABLE_NAME} in region: {AWS_REGION}")
except (NoCredentialsError, PartialCredentialsError) as e:
    logger.error(f"AWS credentials error: {e}")
    logger.error("Please configure AWS credentials using 'aws configure' or set AWS_PROFILE environment variable")
    table = None
except Exception as e:
    logger.error(f"Error initializing DynamoDB: {e}")
    table = None


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def build_cors_headers():
    """Build CORS headers for API responses"""
    return {
        "Access-Control-Allow-Origin": CORS_ORIGIN,
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
        "Access-Control-Allow-Methods": "GET,OPTIONS",
        "Content-Type": "application/json"
    }


def create_response(status_code: int, body: Dict[Any, Any]) -> Dict[str, Any]:
    """Create standardized API response"""
    return {
        "statusCode": status_code,
        "headers": build_cors_headers(),
        "body": json.dumps(body, cls=DecimalEncoder)
    }


def create_error_response(status_code: int, message: str, details: Optional[str] = None) -> Dict[str, Any]:
    """Create standardized error response"""
    error_body = {
        "error": message,
        "status": status_code
    }
    if details:
        error_body["details"] = details
    
    return create_response(status_code, error_body)


def parse_query_params(event: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate query parameters from API Gateway event"""
    params = event.get("queryStringParameters") or {}
    
    parsed = {
        "city": params.get("city"),
        "prop_type": params.get("prop_type"),
        "branch": params.get("branch"),
        "discount": params.get("discount"),
        "min_price": params.get("min_price"),
        "max_price": params.get("max_price"),
        "status": params.get("status", "1"),
        "sort_by": params.get("sort_by", "min_sellprice"),
        "sort_order": params.get("sort_order", "asc"),
        "limit": params.get("limit", "50"),
        "last_key": params.get("last_key"),
    }
    
    # Validate and convert numeric parameters
    try:
        if parsed["min_price"]:
            parsed["min_price"] = float(parsed["min_price"])
        if parsed["max_price"]:
            parsed["max_price"] = float(parsed["max_price"])
        
        parsed["limit"] = int(parsed["limit"])
        if parsed["limit"] < 1 or parsed["limit"] > 100:
            raise ValueError("Limit must be between 1 and 100")
            
    except ValueError as e:
        raise ValueError(f"Invalid parameter: {str(e)}")
    
    # Validate sort order
    if parsed["sort_order"] not in ["asc", "desc"]:
        raise ValueError("sort_order must be 'asc' or 'desc'")
    
    return parsed


def build_filter_expression(params: Dict[str, Any]):
    """Build DynamoDB filter expression from query parameters"""
    filter_expr = None
    
    # City filter (case-insensitive contains)
    if params.get("city"):
        city_filter = Attr("city_muni").contains(params["city"].upper())
        filter_expr = city_filter if filter_expr is None else filter_expr & city_filter
    
    # Property type filter (exact match)
    if params.get("prop_type"):
        type_filter = Attr("prop_type").eq(params["prop_type"])
        filter_expr = type_filter if filter_expr is None else filter_expr & type_filter
    
    # Branch filter (case-insensitive contains)
    if params.get("branch"):
        branch_filter = Attr("branch").contains(params["branch"].upper())
        filter_expr = branch_filter if filter_expr is None else filter_expr & branch_filter
    
    # Discount filter (exact match)
    if params.get("discount"):
        discount_filter = Attr("discount").eq(params["discount"])
        filter_expr = discount_filter if filter_expr is None else filter_expr & discount_filter
    
    # Price range filters
    if params.get("min_price") is not None:
        min_price_filter = Attr("min_sellprice").gte(Decimal(str(params["min_price"])))
        filter_expr = min_price_filter if filter_expr is None else filter_expr & min_price_filter
    
    if params.get("max_price") is not None:
        max_price_filter = Attr("min_sellprice").lte(Decimal(str(params["max_price"])))
        filter_expr = max_price_filter if filter_expr is None else filter_expr & max_price_filter
    
    # Status filter
    if params.get("status"):
        status_filter = Attr("status").eq(params["status"])
        filter_expr = status_filter if filter_expr is None else filter_expr & status_filter
    
    return filter_expr


def sort_items(items: List[Dict], sort_by: str, sort_order: str) -> List[Dict]:
    """Sort items by specified field and order"""
    reverse = (sort_order == "desc")
    
    try:
        # Handle missing values by placing them at the end
        return sorted(
            items,
            key=lambda x: (x.get(sort_by) is None, x.get(sort_by, 0)),
            reverse=reverse
        )
    except Exception as e:
        logger.warning(f"Error sorting by {sort_by}: {e}. Returning unsorted.")
        return items


def encode_last_key(last_key: Dict) -> str:
    """Encode DynamoDB LastEvaluatedKey to base64 string"""
    if not last_key:
        return None
    return base64.b64encode(json.dumps(last_key).encode()).decode()


def decode_last_key(encoded_key: str) -> Dict:
    """Decode base64 string to DynamoDB LastEvaluatedKey"""
    if not encoded_key:
        return None
    try:
        return json.loads(base64.b64decode(encoded_key).decode())
    except Exception as e:
        raise ValueError(f"Invalid pagination token: {str(e)}")


def get_properties(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get list of properties with filters and pagination
    """
    try:
        # Check if DynamoDB is initialized
        if table is None:
            return create_error_response(
                500,
                "Database connection not available",
                "AWS credentials not configured. Run 'aws configure' or set AWS_PROFILE environment variable."
            )
        
        # Build scan parameters
        scan_params = {
            "Limit": params["limit"]
        }
        
        # Add filter expression
        filter_expr = build_filter_expression(params)
        if filter_expr:
            scan_params["FilterExpression"] = filter_expr
        
        # Add pagination token
        if params.get("last_key"):
            scan_params["ExclusiveStartKey"] = decode_last_key(params["last_key"])
        
        # Execute scan
        logger.info(f"Scanning table with params: {scan_params}")
        response = table.scan(**scan_params)
        
        items = response.get("Items", [])
        
        # Sort items
        items = sort_items(items, params["sort_by"], params["sort_order"])
        
        # Prepare response
        result = {
            "items": items,
            "count": len(items),
            "scanned_count": response.get("ScannedCount", 0)
        }
        
        # Add pagination info
        if "LastEvaluatedKey" in response:
            result["last_key"] = encode_last_key(response["LastEvaluatedKey"])
            result["has_more"] = True
        else:
            result["has_more"] = False
        
        logger.info(f"Returning {len(items)} items")
        return create_response(200, result)
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return create_error_response(400, "Invalid request", str(e))
    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return create_error_response(
            500,
            "AWS credentials not configured",
            "Run 'aws configure' to set up your credentials"
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UnrecognizedClientException':
            logger.error(f"Invalid AWS credentials: {e}")
            return create_error_response(
                500,
                "Invalid AWS credentials",
                "Your AWS credentials are invalid or expired. Run 'aws configure' to update them."
            )
        else:
            logger.error(f"AWS error: {e}")
            return create_error_response(500, "AWS service error", str(e))
    except Exception as e:
        logger.error(f"Error getting properties: {e}", exc_info=True)
        return create_error_response(500, "Internal server error", str(e))


def get_property_by_id(property_id: str) -> Dict[str, Any]:
    """
    Get a single property by source_property_id
    """
    try:
        # Check if DynamoDB is initialized
        if table is None:
            return create_error_response(
                500,
                "Database connection not available",
                "AWS credentials not configured. Run 'aws configure' or set AWS_PROFILE environment variable."
            )
        
        if not property_id:
            return create_error_response(400, "Property ID is required")
        
        logger.info(f"Getting property: {property_id}")
        response = table.get_item(Key={"source_property_id": property_id})
        
        if "Item" not in response:
            return create_error_response(404, "Property not found", f"No property with ID: {property_id}")
        
        return create_response(200, {"item": response["Item"]})
        
    except Exception as e:
        logger.error(f"Error getting property {property_id}: {e}", exc_info=True)
        return create_error_response(500, "Internal server error", str(e))


def get_statistics() -> Dict[str, Any]:
    """
    Get aggregated statistics about properties
    """
    try:
        # Check if DynamoDB is initialized
        if table is None:
            return create_error_response(
                500,
                "Database connection not available",
                "AWS credentials not configured. Run 'aws configure' or set AWS_PROFILE environment variable."
            )
        
        logger.info("Calculating statistics...")
        
        # Scan all items (in production, consider using a separate aggregation table)
        response = table.scan()
        items = response.get("Items", [])
        
        # Continue scanning if there are more items
        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            items.extend(response.get("Items", []))
        
        if not items:
            return create_response(200, {
                "total_count": 0,
                "message": "No properties found"
            })
        
        # Calculate statistics
        prices = [float(item.get("min_sellprice", 0)) for item in items if item.get("min_sellprice")]
        
        stats = {
            "total_count": len(items),
            "avg_price": sum(prices) / len(prices) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
        }
        
        # Group by city
        by_city = {}
        for item in items:
            city = item.get("city_muni", "Unknown")
            by_city[city] = by_city.get(city, 0) + 1
        stats["by_city"] = dict(sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Group by property type
        by_type = {}
        for item in items:
            prop_type = item.get("prop_type", "Unknown")
            by_type[prop_type] = by_type.get(prop_type, 0) + 1
        stats["by_type"] = by_type
        
        # Group by discount
        by_discount = {}
        for item in items:
            discount = item.get("discount", "Unknown")
            by_discount[discount] = by_discount.get(discount, 0) + 1
        stats["by_discount"] = by_discount
        
        logger.info(f"Statistics calculated for {len(items)} properties")
        return create_response(200, stats)
        
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}", exc_info=True)
        return create_error_response(500, "Internal server error", str(e))


def handle_options() -> Dict[str, Any]:
    """Handle OPTIONS request for CORS preflight"""
    return {
        "statusCode": 200,
        "headers": build_cors_headers(),
        "body": ""
    }


def route_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route incoming requests to appropriate handlers
    """
    try:
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "/")
        path_params = event.get("pathParameters") or {}
        
        logger.info(f"Routing request: {http_method} {path}")
        
        # Handle OPTIONS for CORS
        if http_method == "OPTIONS":
            return handle_options()
        
        # Route based on path and method
        if http_method == "GET":
            if path == "/properties" or path == "/":
                params = parse_query_params(event)
                return get_properties(params)
            
            elif path == "/properties/stats" or path == "/stats":
                return get_statistics()
            
            elif path.startswith("/properties/"):
                property_id = path_params.get("id") or path.split("/")[-1]
                return get_property_by_id(property_id)
        
        # Method not allowed
        return create_error_response(405, "Method not allowed", f"{http_method} {path}")
    
    except ValueError as e:
        # Handle validation errors from parse_query_params
        logger.error(f"Validation error: {e}")
        return create_error_response(400, "Invalid request", str(e))
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in route_request: {e}", exc_info=True)
        return create_error_response(500, "Internal server error", str(e))

# Made with Bob
