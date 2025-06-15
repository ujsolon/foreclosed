import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import time
import logging
import boto3
import os
from io import BytesIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "https://www.pagibigfundservices.com/OnlinePublicAuction"
API_URL = f"{BASE_URL}/ListofProperties/Load_ListProperties"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": BASE_URL
}

session = requests.Session()

def parse_main_page():
    print("Fetching main page...")
    response = session.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')

    all_records = []
    tab_discounts = {
        "-1": "Properties with no discount (1st auction)",
        "-2": "Properties up to 30% discount (2nd auction)",
        "-3": "Properties up to 45% discount (Negotiated Sale)"
    }

    for tab_id, discount_label in tab_discounts.items():
        tab_div = soup.find("div", id=tab_id)
        if not tab_div:
            continue

        branches = tab_div.find_all("div", class_="batches")
        for branch_div in branches:
            branch_name = branch_div.find("h4").text.strip()

            tranche_entries = branch_div.find_all("div", style=lambda v: v and "padding: 15px 15px" in v)
            for tranche_div in tranche_entries:
                try:
                    raw_html = tranche_div.decode_contents()
                    
                    batch_no = re.search(r'data-batch-no="(.*?)"', raw_html)
                    if not batch_no:
                        continue
                    batch_no = batch_no.group(1)

                    areas = re.search(r"<b>Areas: </b>(.*?)</p>", raw_html)
                    areas_list = [a.strip() for a in areas.group(1).split(",")] if areas else []

                    tranche_number = re.search(r"<b>Tranche Number: </b>(.*?)</p>", raw_html)
                    tranche_number = tranche_number.group(1) if tranche_number else batch_no

                    acceptance = re.search(r"<b>Duration of Acceptance of Bid Offers: </b>(.*?)</p>", raw_html)
                    bid_opening = re.search(r"<b>Opening of Offers: </b>(.*?)</p>", raw_html)

                    bid_start, bid_end = None, None
                    if acceptance:
                        match = re.match(r"([A-Za-z]+\s\d{1,2},\s\d{4}(?:\s\d{1,2}:\d{2}\s[APMapm]{2})?)\s*-\s*([A-Za-z]+\s\d{1,2},\s\d{4}(?:\s\d{1,2}:\d{2}\s[APMapm]{2})?)", acceptance.group(1))
                        if match:
                            bid_start = parse_datetime(match.group(1))
                            bid_end = parse_datetime(match.group(2))

                    bid_open = parse_datetime(bid_opening.group(1)) if bid_opening else None

                    all_records.append({
                        "type": "pag-ibig",
                        "discount": discount_label,
                        "branch": branch_name,
                        "tranche_number": tranche_number,
                        "batch_no": batch_no,
                        "areas": areas_list,
                        "bid_acceptance_start": bid_start,
                        "bid_acceptance_end": bid_end,
                        "opening_of_offers": bid_open,
                    })

                except Exception as e:
                    print(f"Error parsing tranche in branch [{branch_name}] with HTML:\n{tranche_div.prettify()[:300]}\nError: {e}")
                    continue

    return all_records

def parse_datetime(text):
    try:
        return datetime.strptime(text.strip(), "%B %d, %Y %I:%M %p").isoformat()
    except:
        try:
            return datetime.strptime(text.strip(), "%B %d, %Y").isoformat()
        except:
            return text.strip()

def fetch_properties(batch_no):
    params = {"batchno": batch_no, "flag": "1", "ropa_id": ""}
    logging.info(f"📦 Fetching properties for batch {batch_no}...")
    try:
        res = session.get(API_URL, headers=HEADERS, params=params)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"❌ Failed to fetch batch {batch_no}: {e}")
        return []

def enrich_with_properties(batch_meta):
    all_data = []
    updated_on = datetime.utcnow().isoformat() + "Z"

    for i, record in enumerate(batch_meta, 1):
        # print(f"\n🔄 [{i}/{len(batch_meta)}] Enriching batch {record['batch_no']} from branch {record['branch']} ({record['discount']})")
        props = fetch_properties(record["batch_no"])
        for p in props:
            enriched = {**record, **p, "updated_on": updated_on}
            all_data.append(enriched)
        time.sleep(1)
    return all_data

def save_as_json_to_s3(data):
    s3 = boto3.client("s3")
    bucket_name = os.environ.get("RAW_DATA_BUCKET", "raw-data")  # safer with env var
    date_today = datetime.utcnow().strftime("%Y-%m-%d")
    key = f"{date_today}/pagibig.json"

    # Convert Python object to JSON string
    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    
    # Upload to S3
    try:
        s3.put_object(Bucket=bucket_name, Key=key, Body=json_bytes, ContentType="application/json")
        print(f"✅ Saved {len(data)} records to s3://{bucket_name}/{key}")
    except Exception as e:
        print(f"❌ Failed to upload to S3: {e}")

def lambda_handler(event, context):
    meta_data = parse_main_page()
    enriched_data = enrich_with_properties(meta_data)
    save_as_json_to_s3(enriched_data)
    return {
        "statusCode": 200,
        "body": f"{len(enriched_data)} records scraped and uploaded to S3."
    }
