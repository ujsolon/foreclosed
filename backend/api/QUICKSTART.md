# Quick Start Guide - Testing the Property API

This guide will help you quickly test the API Lambda function locally.

## Prerequisites

1. **Python 3.11+** installed
2. **AWS credentials** configured with access to DynamoDB
3. **Data loaded** in DynamoDB table named `properties`

## Step 1: Install Dependencies

```bash
cd backend/api
pip install -r requirements.txt
```

## Step 2: Configure Environment (Optional)

If your DynamoDB table has a different name or is in a different region:

```bash
# Windows (PowerShell)
$env:TABLE_NAME="properties"
$env:AWS_REGION="us-east-1"

# Linux/Mac
export TABLE_NAME=properties
export AWS_REGION=us-east-1
```

## Step 3: Load Sample Data (If Needed)

If you haven't loaded data into DynamoDB yet, run the loader:

```bash
cd ../loader
python loader.py
```

This will load data from `data/test.json` into DynamoDB.

## Step 4: Run the Test Script

```bash
cd ../api
python test_api.py
```

## Expected Output

You should see colorful output like this:

```
============================================================
                    Property API Test Suite                    
============================================================

🧪 Testing: List all properties (default pagination)
✅ Retrieved 50 properties
   Has more: True
   Scanned: 50

🧪 Testing: Filter properties by city (ROXAS)
✅ Found 5 properties in ROXAS

🧪 Testing: Filter properties by type (Lot Only)
✅ Found 30 'Lot Only' properties

🧪 Testing: Filter properties by price range (500k - 1M)
✅ Found 15 properties in price range

🧪 Testing: Multiple filters (city + type + price)
✅ Found 2 properties matching all filters

🧪 Testing: Sort by price (ascending)
✅ Properties correctly sorted by price (asc)
   Price range: 100000.0 - 500000.0

🧪 Testing: Pagination (fetch 2 pages)
   Page 1: 3 items
   Page 2: 3 items
✅ Pagination working correctly (no duplicates)

🧪 Testing: Get property by ID
   Testing with ID: pagibig_858202309280002
✅ Retrieved property: pagibig_858202309280002
   Location: Lot 3795-D-3-E Blk. PSD-411410 CAGAY, ROXAS CITY, CAPIZ, 5800
   Price: 915200

🧪 Testing: Get non-existent property (should return 404)
✅ Correctly returned 404 for non-existent property

🧪 Testing: Get statistics
✅ Statistics retrieved successfully
   Total properties: 1234
   Average price: ₱850,000.50
   Price range: ₱100,000 - ₱5,000,000
   Top cities: ['ROXAS CITY', 'MANILA', 'QUEZON CITY']

🧪 Testing: Invalid parameters (should return 400)
✅ Correctly rejected invalid limit
✅ Correctly rejected invalid price

🧪 Testing: CORS headers
✅ CORS headers present
   Origin: *

============================================================
                        Test Summary                        
============================================================
Total tests: 12
✅ Passed: 12
✅ All tests passed! 🎉
```

## Troubleshooting

### Error: "Table not found"

**Problem:** DynamoDB table doesn't exist or has a different name.

**Solution:**
```bash
# Check your table name in AWS Console, then set it:
export TABLE_NAME=your_actual_table_name
```

### Error: "No credentials found"

**Problem:** AWS credentials not configured.

**Solution:**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### Error: "No properties available to test"

**Problem:** DynamoDB table is empty.

**Solution:**
```bash
# Load sample data
cd ../loader
python loader.py
```

### Error: "Access Denied"

**Problem:** IAM permissions insufficient.

**Solution:** Ensure your AWS user/role has these permissions:
- `dynamodb:GetItem`
- `dynamodb:Scan`
- `dynamodb:Query`

## Testing Individual Endpoints

You can also test individual endpoints manually:

### Test List Properties
```python
from lambda_function import lambda_handler

event = {
    "httpMethod": "GET",
    "path": "/properties",
    "queryStringParameters": {"limit": "10"},
    "pathParameters": None
}

response = lambda_handler(event, None)
print(response)
```

### Test Get Property by ID
```python
event = {
    "httpMethod": "GET",
    "path": "/properties/pagibig_858202309280002",
    "queryStringParameters": None,
    "pathParameters": {"id": "pagibig_858202309280002"}
}

response = lambda_handler(event, None)
print(response)
```

### Test Statistics
```python
event = {
    "httpMethod": "GET",
    "path": "/properties/stats",
    "queryStringParameters": None,
    "pathParameters": None
}

response = lambda_handler(event, None)
print(response)
```

## Next Steps

After successful testing:

1. **Deploy to AWS Lambda**
   ```bash
   cd ../../infra
   # Create Lambda deployment package
   cd ../backend/api
   zip -r ../../infra/api_lambda.zip .
   
   # Deploy with Terraform
   cd ../../infra
   terraform apply
   ```

2. **Set up API Gateway** to expose the Lambda function as a REST API

3. **Connect Frontend** to the API endpoints

4. **Add monitoring** with CloudWatch Logs and Metrics

## API Endpoints Summary

Once deployed, your API will support:

- `GET /properties` - List properties with filters
- `GET /properties/{id}` - Get single property
- `GET /properties/stats` - Get statistics

See [README.md](README.md) for complete API documentation.

## Support

If you encounter issues:

1. Check the test output for specific error messages
2. Review [README.md](README.md) for detailed documentation
3. Check CloudWatch Logs if deployed to AWS
4. Verify DynamoDB table has data and correct permissions

## Performance Tips

For better test performance:

1. **Use smaller limits** during testing: `?limit=5`
2. **Test with specific filters** to reduce scan size
3. **Run tests against local DynamoDB** for faster iteration (requires DynamoDB Local)

## Local DynamoDB (Optional)

For faster testing without AWS costs:

```bash
# Install DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Update endpoint in main.py
dynamodb = boto3.resource("dynamodb", 
    region_name=AWS_REGION,
    endpoint_url="http://localhost:8000"
)