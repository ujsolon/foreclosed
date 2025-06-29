# Foreclosed Property Scraper & Search UI

Website: [https://my-foreclosed-site.s3.us-east-1.amazonaws.com/index.html](https://my-foreclosed-site.s3.us-east-1.amazonaws.com/index.html)

---

## Overview

This project scrapes Pag-IBIG Fund foreclosed property auctions, detects changes, and loads enriched property data into AWS DynamoDB. It provides a React-based search UI and is fully deployable on AWS using Terraform.

---

## Features

- **Python Scraper** (`backend/scraper/`): Extracts and enriches Pag-IBIG property auction data.
- **Change Watcher** (`backend/watcher/`): Detects changes in auction listings and triggers scrapes.
- **Loader** (`backend/loader/`): Loads JSON property data into DynamoDB, with update detection.
- **API Lambda** (`backend/api/`): Simple AWS Lambda API endpoint.
- **React Frontend** (`frontend/`): Search UI for foreclosed properties.
- **Terraform Infrastructure** (`infra/`): Provisions S3, CloudFront, DynamoDB, Lambda, and related IAM roles/policies.

---

## Project Structure

```
main.py                  # Legacy scraper entry point
backend/
  api/                   # Lambda API handler
  loader/                # DynamoDB loader (batch + Lambda)
  scraper/               # Scraper logic (batch + Lambda)
  watcher/               # Change detection logic (batch + Lambda)
data/
  pagibig_enriched.json  # Scraped/enriched property data
  ...                    # Other data files
frontend/
  src/
    components/ui/       # UI components (Button, SearchBar, etc.)
    App.js               # Main React app
infra/
  *.tf                   # Terraform configs for AWS resources
  terraform.md           # Infra deployment notes
```

---

## Usage

### 1. Scraping Pag-IBIG Properties

Install dependencies:

```sh
pip install -r requirements.txt
```

Run the scraper (legacy):

```sh
python main.py
```

Or use the modular backend:

```sh
python backend/scraper/scraper.py
```

Output: `pagibig_enriched.json` in the `data/` folder or upload to S3.

---

### 2. Loading Data to DynamoDB

Update `backend/loader/loader.py` config for your S3 bucket/object/table.

Run locally:

```sh
python backend/loader/loader.py
```

Or deploy as Lambda (see infra).

---

### 3. Frontend (React)

```sh
cd frontend
npm install
npm start
```

Build for production:

```sh
npm run build
```

---

### 4. Infrastructure (Terraform)

See [`infra/terraform.md`](infra/terraform.md) for detailed AWS setup.

Typical workflow:

```sh
cd infra
terraform init
terraform plan
terraform apply
```

**Note:** Lambda functions are zipped from `backend/` and uploaded as artifacts (see `terraform.md` for zip commands).

---

## AWS Architecture

- **S3**: Hosts frontend and raw data.
- **CloudFront**: CDN for frontend.
- **DynamoDB**: Stores property records.
- **Lambda**: Scraper, loader, watcher, and API endpoints.
- **IAM**: Fine-grained roles for Lambda and Terraform.

---

## Data Files

- `data/pagibig_enriched.json`: Main output from scraper.
- `data_source.json`, `pagibig_properties_v1.json`, `test.json`: Other data sources.

---

## Deployment

- Website: [https://my-foreclosed-site.s3.us-east-1.amazonaws.com/index.html](https://my-foreclosed-site.s3.us-east-1.amazonaws.com/index.html)
- All AWS resources managed via Terraform in [`infra/`](infra/)

---

## License

MIT