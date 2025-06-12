import boto3
import json
from decimal import Decimal
import os

# Adjust directory path as needed
base_dir = os.path.dirname(__file__)  # Directory of the current script


# --- Configuration ---
file_source = os.path.join(base_dir, "data", "test.json")
table_name = "properties"
region_name = "us-east-1"   # or your region
profile_name = "default"    # from your AWS CLI

# --- AWS Session ---
session = boto3.Session(profile_name=profile_name, region_name=region_name)
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(table_name)

# --- Load Data from JSON File ---
with open(file_source, "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert all floats to Decimal (required by DynamoDB)
data = [json.loads(json.dumps(item), parse_float=Decimal) for item in data]

# --- Batch Upload ---
with table.batch_writer(overwrite_by_pkeys=['batch_no', 'ropa_id']) as batch:
    for i, item in enumerate(data, 1):
        try:
            batch.put_item(Item=item)
            print(f"✅ Uploaded {i}/{len(data)}: {item['batch_no']} - {item['ropa_id']}")
        except Exception as e:
            print(f"❌ Error uploading item {item.get('ropa_id')}: {e}")
