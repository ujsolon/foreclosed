import boto3
import json
from decimal import Decimal
from datetime import datetime
import os
import logging

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
bucket_name = "foreclosed-raw-data"
object_key = "test.json"
table_name = "properties"
region_name = "us-east-1"
profile_name = os.getenv("AWS_PROFILE", "default")

# --- Batch Configuration ---
BATCH_GET_SIZE = 100  # DynamoDB batch_get_item limit
BATCH_WRITE_SIZE = 25  # DynamoDB batch_write_item limit


def batch_get_existing_items(dynamodb, table_name, keys):
    """
    Get multiple items from DynamoDB in batches.
    
    Args:
        dynamodb: boto3 DynamoDB resource
        table_name: Name of the DynamoDB table
        keys: List of key dictionaries
    
    Returns:
        Dictionary mapping source_property_id to existing items
    """
    existing_items = {}
    
    if not keys:
        return existing_items
    
    logger.info(f"Batch fetching {len(keys)} existing items...")
    
    for i in range(0, len(keys), BATCH_GET_SIZE):
        batch_keys = keys[i:i + BATCH_GET_SIZE]
        
        try:
            response = dynamodb.batch_get_item(
                RequestItems={
                    table_name: {
                        'Keys': batch_keys
                    }
                }
            )
            
            for item in response.get('Responses', {}).get(table_name, []):
                existing_items[item['source_property_id']] = item
            
            # Handle unprocessed keys
            unprocessed = response.get('UnprocessedKeys', {})
            if unprocessed:
                logger.warning(f"Unprocessed keys in batch {i//BATCH_GET_SIZE + 1}: {len(unprocessed)}")
                
        except Exception as e:
            logger.error(f"Error in batch_get_item (batch {i//BATCH_GET_SIZE + 1}): {e}")
    
    logger.info(f"Found {len(existing_items)} existing items")
    return existing_items


def batch_write_items(table, items_to_write, operation_type="write"):
    """
    Write multiple items to DynamoDB in batches.
    
    Args:
        table: DynamoDB table resource
        items_to_write: List of items to write
        operation_type: Type of operation for logging (add/update)
    
    Returns:
        Tuple of (success_count, failed_items)
    """
    if not items_to_write:
        return 0, []
    
    success_count = 0
    failed_items = []
    
    logger.info(f"Batch writing {len(items_to_write)} items ({operation_type})...")
    
    for i in range(0, len(items_to_write), BATCH_WRITE_SIZE):
        batch = items_to_write[i:i + BATCH_WRITE_SIZE]
        
        try:
            with table.batch_writer() as writer:
                for item in batch:
                    writer.put_item(Item=item)
                    success_count += 1
                    
        except Exception as e:
            logger.error(f"Batch write failed (batch {i//BATCH_WRITE_SIZE + 1}): {e}")
            # Track all items in failed batch
            for item in batch:
                failed_items.append({
                    "source_property_id": item.get("source_property_id", "UNKNOWN"),
                    "ropa_id": item.get("ropa_id", "UNKNOWN"),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "operation": operation_type
                })
    
    logger.info(f"Successfully wrote {success_count} items ({operation_type})")
    return success_count, failed_items


def needs_update(new_item, existing_item):
    """
    Check if an item needs to be updated by comparing all fields
    except timestamps.
    
    Args:
        new_item: New item data
        existing_item: Existing item from DynamoDB
    
    Returns:
        Boolean indicating if update is needed
    """
    exclude_fields = {"updated_on", "created_on"}
    
    for key in new_item:
        if key in exclude_fields:
            continue
        if new_item.get(key) != existing_item.get(key):
            return True
    
    return False


def process_data(session):
    """
    Main processing function with enhanced error handling and batch operations.
    
    Returns:
        Dictionary with processing summary and error details
    """
    s3 = session.client("s3")
    dynamodb_client = session.client("dynamodb")
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(table_name)
    
    # Counters
    added_count = 0
    updated_count = 0
    unchanged_count = 0
    validation_errors = []
    processing_errors = []
    
    try:
        # --- Step 1: Load data from S3 ---
        logger.info(f"Loading '{object_key}' from bucket '{bucket_name}'")
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        content = response["Body"].read().decode("utf-8")
        data = json.loads(content)
        
        logger.info(f"Loaded {len(data)} items from S3")
        
        # Convert floats to Decimal for DynamoDB
        data = [json.loads(json.dumps(item), parse_float=Decimal) for item in data]
        
    except Exception as e:
        logger.error(f"Failed to load data from S3: {e}")
        return {
            "statusCode": 500,
            "body": {
                "error": "Failed to load data from S3",
                "error_message": str(e),
                "error_type": type(e).__name__
            }
        }
    
    # --- Step 2: Validate and prepare items ---
    valid_items = []
    keys_to_fetch = []
    
    for i, item in enumerate(data, 1):
        # Validate required field
        if "ropa_id" not in item:
            validation_errors.append({
                "index": i,
                "error": "missing_ropa_id",
                "item_preview": str(item)[:200]
            })
            logger.warning(f"Skipping item {i} (missing ropa_id)")
            continue
        
        # Generate source_property_id
        item["source_property_id"] = f"pagibig_{item['ropa_id']}"
        valid_items.append(item)
        keys_to_fetch.append({"source_property_id": item["source_property_id"]})
    
    logger.info(f"Validated {len(valid_items)} items, {len(validation_errors)} validation errors")
    
    if not valid_items:
        logger.warning("No valid items to process")
        return {
            "statusCode": 400,
            "body": {
                "summary": {
                    "added": 0,
                    "updated": 0,
                    "unchanged": 0,
                    "failed": 0,
                    "validation_errors": len(validation_errors),
                    "total": len(data)
                },
                "validation_errors": validation_errors[:10],
                "message": "No valid items to process"
            }
        }
    
    # --- Step 3: Batch get existing items ---
    try:
        existing_items = batch_get_existing_items(dynamodb_client, table_name, keys_to_fetch)
    except Exception as e:
        logger.error(f"Failed to fetch existing items: {e}")
        processing_errors.append({
            "stage": "batch_get",
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        # Continue with empty existing_items to treat all as new
        existing_items = {}
    
    # --- Step 4: Categorize items (add/update/unchanged) ---
    items_to_add = []
    items_to_update = []
    unchanged_items = []
    
    current_timestamp = datetime.utcnow().isoformat()
    
    for item in valid_items:
        source_id = item["source_property_id"]
        existing = existing_items.get(source_id)
        
        try:
            if not existing:
                # New item - add created_on timestamp
                item["created_on"] = current_timestamp
                items_to_add.append(item)
                
            elif needs_update(item, existing):
                # Changed item - add updated_on timestamp
                item["updated_on"] = current_timestamp
                # Preserve created_on from existing item
                if "created_on" in existing:
                    item["created_on"] = existing["created_on"]
                items_to_update.append(item)
                
            else:
                # Unchanged item
                unchanged_items.append(source_id)
                
        except Exception as e:
            processing_errors.append({
                "source_property_id": source_id,
                "ropa_id": item.get("ropa_id", "UNKNOWN"),
                "stage": "categorization",
                "error_type": type(e).__name__,
                "error_message": str(e)
            })
            logger.error(f"Error categorizing item {source_id}: {e}")
    
    unchanged_count = len(unchanged_items)
    
    logger.info(f"Categorized: {len(items_to_add)} to add, {len(items_to_update)} to update, {unchanged_count} unchanged")
    
    # --- Step 5: Batch write items ---
    add_failures = []
    update_failures = []
    
    if items_to_add:
        added_count, add_failures = batch_write_items(table, items_to_add, "add")
    
    if items_to_update:
        updated_count, update_failures = batch_write_items(table, items_to_update, "update")
    
    # Combine all failures
    all_failures = add_failures + update_failures + processing_errors
    
    # --- Step 6: Generate summary ---
    logger.info("\n--- Summary ---")
    logger.info(f"✅ Added: {added_count}")
    logger.info(f"🔁 Updated: {updated_count}")
    logger.info(f"⏩ Unchanged: {unchanged_count}")
    logger.info(f"❌ Failed: {len(all_failures)}")
    logger.info(f"⚠️  Validation Errors: {len(validation_errors)}")
    logger.info(f"📦 Total Processed: {len(data)}")
    
    # Determine status code
    if all_failures or validation_errors:
        status_code = 207  # Multi-Status (partial success)
    else:
        status_code = 200  # Complete success
    
    return {
        "statusCode": status_code,
        "body": {
            "summary": {
                "added": added_count,
                "updated": updated_count,
                "unchanged": unchanged_count,
                "failed": len(all_failures),
                "validation_errors": len(validation_errors),
                "total": len(data),
                "success_rate": round((added_count + updated_count + unchanged_count) / len(data) * 100, 2) if data else 0
            },
            "failed_items": all_failures[:10] if all_failures else [],
            "validation_errors": validation_errors[:10] if validation_errors else [],
            "has_more_errors": len(all_failures) > 10 or len(validation_errors) > 10,
            "timestamp": current_timestamp
        }
    }


def lambda_handler(event, context):
    """
    Lambda handler function.
    
    Args:
        event: Lambda event (can contain S3 trigger info)
        context: Lambda context
    
    Returns:
        Processing result dictionary
    """
    try:
        session = boto3.Session(region_name=region_name)
        result = process_data(session)
        
        # Log final result
        logger.info(f"Processing complete with status {result['statusCode']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Unhandled exception in lambda_handler: {e}", exc_info=True)
        return {
            "statusCode": 500,
            "body": {
                "error": "Internal server error",
                "error_type": type(e).__name__,
                "error_message": str(e)
            }
        }


if __name__ == "__main__":
    result = lambda_handler(None, None)
    print("\n" + "="*50)
    print("FINAL RESULT:")
    print(json.dumps(result, indent=2, default=str))
    print("="*50)

# Made with Bob
