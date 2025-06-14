import boto3
import json
from decimal import Decimal
from datetime import datetime
import os

# --- Configuration ---
base_dir = os.path.dirname(__file__)
file_source = os.path.join(base_dir, "test.json")
table_name = "properties"
region_name = "us-east-1"
profile_name = "default"

# --- AWS Session ---
session = boto3.Session(profile_name=profile_name, region_name=region_name)
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(table_name)

# --- Load Data ---
with open(file_source, "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert all floats to Decimal
data = [json.loads(json.dumps(item), parse_float=Decimal) for item in data]

# --- Counters ---
added_count = 0
updated_count = 0
unchanged_count = 0

# --- Processing Items ---
for i, item in enumerate(data, 1):
    key = {
        "batch_no": item["batch_no"],
        "ropa_id": item["ropa_id"]
    }

    try:
        # Retrieve existing item
        response = table.get_item(Key=key)
        existing_item = response.get("Item")

        if not existing_item:
            # New item — insert directly
            item["updated_on"] = datetime.utcnow().isoformat()
            table.put_item(Item=item)
            added_count += 1
            print(f"🆕 Added {i}: {key}")
            continue

        # Compare fields (excluding updated_on)
        needs_update = False
        for k, v in item.items():
            if k == "updated_on":
                continue
            if existing_item.get(k) != v:
                needs_update = True
                break

        if needs_update:
            item["updated_on"] = datetime.utcnow().isoformat()
            table.put_item(Item=item)
            updated_count += 1
            print(f"🔁 Updated {i}: {key}")
        else:
            unchanged_count += 1
            print(f"⏩ Skipped {i}: {key} (no change)")

    except Exception as e:
        print(f"❌ Error on {i}: {key} -> {e}")

# --- Summary ---
print("\n--- Summary ---")
print(f"✅ Added: {added_count}")
print(f"🔁 Updated: {updated_count}")
print(f"⏩ Unchanged: {unchanged_count}")
print(f"📦 Total Processed: {len(data)}")
