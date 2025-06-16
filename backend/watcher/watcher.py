import hashlib
import json
import boto3
import os
from datetime import datetime
from backend.scraper.scraper import parse_main_page, lambda_handler as run_scraper

s3 = boto3.client("s3")
BUCKET = os.environ.get("FORECLOSED_RAW_DATA_BUCKET", "foreclosed-raw-data")
LATEST_KEY = "latest/pagibig_main_page.json"

def compute_hash(data):
    # Only hash relevant parts (e.g., batch_no and acceptance dates)
    filtered = [{k: v for k, v in d.items() if k in ['batch_no', 'bid_acceptance_start', 'bid_acceptance_end', 'opening_of_offers']} for d in data]
    return hashlib.sha256(json.dumps(filtered, sort_keys=True).encode('utf-8')).hexdigest()

def load_latest_data():
    try:
        print("📥 Loading previous data from S3...")
        response = s3.get_object(Bucket=BUCKET, Key=LATEST_KEY)
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        print(f"⚠️ No previous data found or error: {e}")
        return None

def save_latest_data(data):
    s3.put_object(
        Bucket=BUCKET,
        Key=LATEST_KEY,
        Body=json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'),
        ContentType='application/json'
    )

def detect_changes(old_data, new_data):
    old_ids = {d["batch_no"] for d in old_data}
    new_ids = {d["batch_no"] for d in new_data}

    added = new_ids - old_ids
    removed = old_ids - new_ids
    unchanged = old_ids & new_ids

    changes = []
    for b in unchanged:
        old = next(d for d in old_data if d["batch_no"] == b)
        new = next(d for d in new_data if d["batch_no"] == b)
        if old != new:
            changes.append(b)

    return {
        "added": list(added),
        "removed": list(removed),
        "updated": changes
    }

def lambda_handler(event=None, context=None):
    print("🚀 Watcher started...")
    new_data = parse_main_page()
    old_data = load_latest_data()

    if not old_data:
        print("📂 No previous data found. First-time run.")
        run_scraper(event, context)
        save_latest_data(new_data)
        return {
            "statusCode": 200,
            "body": "First run completed. Data scraped and saved."
        }

    if compute_hash(old_data) == compute_hash(new_data):
        print("✅ No changes detected. Skipping scraper.")
        return {
            "statusCode": 200,
            "body": "No updates found."
        }

    print("🔍 Detected changes.")
    changes = detect_changes(old_data, new_data)
    print(f"➕ Added batches: {changes['added']}")
    print(f"➖ Removed batches: {changes['removed']}")
    print(f"♻️ Updated batches: {changes['updated']}")

    run_scraper(event, context)
    save_latest_data(new_data)

    return {
        "statusCode": 200,
        "body": f"Changes detected. Scraper triggered. {len(changes['added'])} added, {len(changes['removed'])} removed, {len(changes['updated'])} updated."
    }

if __name__ == "__main__":
    lambda_handler()