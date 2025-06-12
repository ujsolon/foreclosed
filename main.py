import requests
from bs4 import BeautifulSoup
import json
import time

# Headers for mimicking a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/137.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": "https://www.pagibigfundservices.com/OnlinePublicAuction"
}

SESSION = requests.Session()

# 1. Get the main page HTML
def get_batch_ids(url):
    print("Fetching main page...")
    res = SESSION.get(url, headers=HEADERS)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, 'html.parser')
    buttons = soup.select('.see-list-btn')
    batch_ids = [(btn['data-batch-no'], btn['data-disposal-flag']) for btn in buttons]
    print(f"Found {len(batch_ids)} batch numbers.")
    return batch_ids

# 2. Query the API endpoint per batch number
def get_property_data(batch_id):
    url = f"https://www.pagibigfundservices.com/OnlinePublicAuction/ListofProperties/Load_ListProperties"
    params = {
        "batchno": batch_id,
        "flag": "1",
        "ropa_id": ""
    }
    print(f"Fetching properties for batch {batch_id}...")
    response = SESSION.get(url, headers=HEADERS, params=params)
    response.raise_for_status()
    return response.json()

# 3. Run the full pipeline
def scrape_all_batches():
    master_data = []
    batch_ids = get_batch_ids("https://www.pagibigfundservices.com/OnlinePublicAuction")

    for batch_id, _ in batch_ids:
        try:
            data = get_property_data(batch_id)
            for item in data:
                item['batch_no'] = batch_id
            master_data.extend(data)
            time.sleep(1)  # polite delay
        except Exception as e:
            print(f"Error with batch {batch_id}: {e}")
            continue

    print(f"Collected {len(master_data)} total property records.")
    return master_data

# 4. Save to JSON
def save_to_json(data, filename="pagibig_properties.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"Saved data to {filename}")

if __name__ == "__main__":
    data = scrape_all_batches()
    save_to_json(data)
