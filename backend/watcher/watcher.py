import hashlib
import json
import boto3
import os
from datetime import datetime
from backend.scraper.scraper import parse_main_page, lambda_handler as run_scraper
import logging

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

s3 = boto3.client("s3")
BUCKET = os.environ.get("FORECLOSED_RAW_DATA_BUCKET", "foreclosed-raw-data")
LATEST_KEY = "latest/pagibig_main_page.json"

def compute_hash(data):
    filtered = [{k: v for k, v in d.items() if k in ['batch_no', 'bid_acceptance_start', 'bid_acceptance_end', 'opening_of_offers']} for d in data]
    return hashlib.sha256(json.dumps(filtered, sort_keys=True).encode('utf-8')).hexdigest()

def load_latest_data():
    try:
        logger.info("📥 Loading previous data from S3...")
        response = s3.get_object(Bucket=BUCKET, Key=LATEST_KEY)
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        logger.warning(f"⚠️ No previous data found or error: {e}")
        return None

def save_latest_data(data):
    s3.put_object(
        Bucket=BUCKET,
        Key=LATEST_KEY,
        Body=json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'),
        ContentType='application/json'
    )
    logger.info(f"📤 Saved current snapshot to s3://{BUCKET}/{LATEST_KEY}")

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
    logger.info("🚀 Watcher started...")
    new_data = parse_main_page()
    old_data = load_latest_data()

    if not old_data:
        logger.info("📂 No previous data found. First-time run.")
        run_scraper(event, context)
        save_latest_data(new_data)
        return {
            "statusCode": 200,
            "body": "First run completed. Data scraped and saved."
        }

    if compute_hash(old_data) == compute_hash(new_data):
        logger.info("✅ No changes detected. Skipping scraper.")
        return {
            "statusCode": 200,
            "body": "No updates found."
        }

    logger.info("🔍 Detected changes.")
    changes = detect_changes(old_data, new_data)
    logger.info(f"➕ Added batches: {changes['added']}")
    logger.info(f"➖ Removed batches: {changes['removed']}")
    logger.info(f"♻️ Updated batches: {changes['updated']}")

    run_scraper(event, context)
    save_latest_data(new_data)

    return {
        "statusCode": 200,
        "body": f"Changes detected. Scraper triggered. {len(changes['added'])} added, {len(changes['removed'])} removed, {len(changes['updated'])} updated."
    }

if __name__ == "__main__":
    lambda_handler()
