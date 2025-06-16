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
profile_name = "default"

def main():
    # --- AWS Session ---
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    s3 = session.client("s3")
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # --- Load Data from S3 ---
    logger.info(f"Loading '{object_key}' from bucket '{bucket_name}'")
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    content = response["Body"].read().decode("utf-8")
    data = json.loads(content)

    # Convert all floats to Decimal
    data = [json.loads(json.dumps(item), parse_float=Decimal) for item in data]

    # --- Counters ---
    added_count = 0
    updated_count = 0
    unchanged_count = 0

    # --- Processing Items ---
    for i, item in enumerate(data, 1):
        try:
            # Normalize source_property_id
            if "ropa_id" not in item:
                logger.warning(f"Skipping item {i} (missing ropa_id): {item}")
                continue
            item["source_property_id"] = f"pagibig_{item['ropa_id']}"

            key = {
                "source_property_id": item["source_property_id"]
            }

            # Check existing item
            response = table.get_item(Key=key)
            existing_item = response.get("Item")

            if not existing_item:
                item["created_on"] = datetime.utcnow().isoformat()
                table.put_item(Item=item)
                added_count += 1
                logger.info(f"🆕 Added {i}: {item['source_property_id']}")
                continue

            # Compare fields
            needs_update = False
            for k, v in item.items():
                if k in ("updated_on", "created_on"):
                    continue
                if existing_item.get(k) != v:
                    needs_update = True
                    break

            if needs_update:
                item["updated_on"] = datetime.utcnow().isoformat()
                table.put_item(Item=item)
                updated_count += 1
                logger.info(f"🔁 Updated {i}: {item['source_property_id']}")
            else:
                unchanged_count += 1
                logger.info(f"⏩ Skipped {i}: {item['source_property_id']} (no change)")

        except Exception as e:
            logger.error(f"❌ Error on {i}: {item.get('source_property_id', 'UNKNOWN')} -> {e}")

    # --- Summary ---
    logger.info("\n--- Summary ---")
    logger.info(f"✅ Added: {added_count}")
    logger.info(f"🔁 Updated: {updated_count}")
    logger.info(f"⏩ Unchanged: {unchanged_count}")
    logger.info(f"📦 Total Processed: {len(data)}")

if __name__ == "__main__":
    main()
