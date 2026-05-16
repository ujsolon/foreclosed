# Property API Documentation

A RESTful API for querying foreclosed properties from DynamoDB with comprehensive filtering, sorting, and pagination capabilities.

## Table of Contents
- [Setup](#setup)
- [Testing](#testing)
- [API Endpoints](#api-endpoints)
- [Query Parameters](#query-parameters)
- [Response Format](#response-format)
- [Error Handling](#error-handling)
- [Examples](#examples)

## Setup

### Prerequisites
- Python 3.11+
- AWS credentials configured
- DynamoDB table named `properties` with data loaded

### Installation

```bash
cd backend/api
pip install -r requirements.txt
```

### Environment Variables

```bash
export TABLE_NAME=properties          # DynamoDB table name
export AWS_REGION=us-east-1          # AWS region
export CORS_ORIGIN=*                 # CORS allowed origin
```

## Testing

Run the comprehensive test suite:

```bash
cd backend/api
python test_api.py
```

The test script will:
- Test all API endpoints
- Verify filtering and sorting
- Test pagination
- Validate error handling
- Check CORS headers

## API Endpoints

### 1. List Properties
**GET** `/properties`

Retrieve a list of properties with optional filters, sorting, and pagination.

**Query Parameters:**
- `city` - Filter by city/municipality (case-insensitive, partial match)
- `prop_type` - Filter by property type (exact match)
- `branch` - Filter by branch name (case-insensitive, partial match)
- `discount` - Filter by discount level (exact match)
- `min_price` - Minimum selling price (inclusive)
- `max_price` - Maximum selling price (inclusive)
- `status` - Filter by status (default: "1")
- `sort_by` - Sort field (default: "min_sellprice")
- `sort_order` - Sort direction: "asc" or "desc" (default: "asc")
- `limit` - Results per page (default: 50, max: 100)
- `last_key` - Pagination token (base64 encoded)

**Response:**
```json
{
  "items": [...],
  "count": 50,
  "scanned_count": 75,
  "has_more": true,
  "last_key": "eyJzb3VyY2VfcHJvcGVydHlfaWQiOiAicGFnaWJpZ184NTgyMDIzMDkyODAwMDIifQ=="
}
```

### 2. Get Property by ID
**GET** `/properties/{id}`

Retrieve a single property by its `source_property_id`.

**Path Parameters:**
- `id` - The source_property_id (e.g., "pagibig_858202309280002")

**Response:**
```json
{
  "item": {
    "source_property_id": "pagibig_858202309280002",
    "prop_location": "Lot 3795-D-3-E Blk. PSD-411410 CAGAY, ROXAS CITY, CAPIZ, 5800",
    "prop_type": "Lot Only",
    "min_sellprice": 915200,
    "city_muni": "ROXAS CITY",
    ...
  }
}
```

### 3. Get Statistics
**GET** `/properties/stats`

Get aggregated statistics about all properties.

**Response:**
```json
{
  "total_count": 1234,
  "avg_price": 850000.50,
  "min_price": 100000,
  "max_price": 5000000,
  "by_city": {
    "MANILA": 150,
    "QUEZON CITY": 120,
    ...
  },
  "by_type": {
    "Lot Only": 500,
    "House and Lot": 400,
    ...
  },
  "by_discount": {
    "Properties with no discount (1st auction)": 800,
    "Properties up to 30% discount (2nd auction)": 300,
    ...
  }
}
```

## Query Parameters

### Filtering

#### By Location
```
GET /properties?city=ROXAS
GET /properties?city=MANILA&branch=MAKATI
```

#### By Property Type
```
GET /properties?prop_type=Lot Only
GET /properties?prop_type=House and Lot
```

#### By Price Range
```
GET /properties?min_price=500000&max_price=1000000
GET /properties?max_price=750000
```

#### By Discount Level
```
GET /properties?discount=Properties with no discount (1st auction)
GET /properties?discount=Properties up to 30% discount (2nd auction)
```

#### Multiple Filters
```
GET /properties?city=ROXAS&prop_type=Lot Only&min_price=500000&max_price=1000000
```

### Sorting

```
GET /properties?sort_by=min_sellprice&sort_order=asc
GET /properties?sort_by=min_sellprice&sort_order=desc
GET /properties?sort_by=city_muni&sort_order=asc
```

### Pagination

```
# First page
GET /properties?limit=20

# Next page (use last_key from previous response)
GET /properties?limit=20&last_key=eyJzb3VyY2VfcHJvcGVydHlfaWQiOiAicGFnaWJpZ184NTgyMDIzMDkyODAwMDIifQ==
```

## Response Format

### Success Response
```json
{
  "items": [...],
  "count": 50,
  "has_more": true
}
```

### Error Response
```json
{
  "error": "Invalid request",
  "status": 400,
  "details": "Limit must be between 1 and 100"
}
```

## Error Handling

### HTTP Status Codes

- **200 OK** - Request successful
- **400 Bad Request** - Invalid parameters or validation error
- **404 Not Found** - Property ID not found
- **405 Method Not Allowed** - Invalid HTTP method
- **500 Internal Server Error** - Server error

### Common Errors

#### Invalid Limit
```json
{
  "error": "Invalid request",
  "status": 400,
  "details": "Limit must be between 1 and 100"
}
```

#### Invalid Price
```json
{
  "error": "Invalid request",
  "status": 400,
  "details": "Invalid parameter: could not convert string to float: 'abc'"
}
```

#### Property Not Found
```json
{
  "error": "Property not found",
  "status": 404,
  "details": "No property with ID: nonexistent_id"
}
```

## Examples

### Example 1: Find affordable lots in Roxas City

```bash
curl "https://api.example.com/properties?city=ROXAS&prop_type=Lot%20Only&max_price=600000&sort_by=min_sellprice&sort_order=asc&limit=10"
```

**Response:**
```json
{
  "items": [
    {
      "source_property_id": "pagibig_858202309280005",
      "prop_location": "Lot 2 Blk. 7 Phase 1 HAPPY HOMES SUBDIVISION SIBAGUAN, ROXAS CITY, CAPIZ, 5800",
      "prop_type": "Lot Only",
      "min_sellprice": 560000,
      "lot_area": "80",
      "city_muni": "ROXAS CITY",
      "branch": "BACOLOD BRANCH",
      "discount": "Properties with no discount (1st auction)"
    }
  ],
  "count": 1,
  "has_more": false
}
```

### Example 2: Get property details

```bash
curl "https://api.example.com/properties/pagibig_858202309280002"
```

**Response:**
```json
{
  "item": {
    "source_property_id": "pagibig_858202309280002",
    "type": "pag-ibig",
    "discount": "Properties with no discount (1st auction)",
    "branch": "BACOLOD BRANCH",
    "prop_location": "Lot 3795-D-3-E Blk. PSD-411410 CAGAY, ROXAS CITY, CAPIZ, 5800",
    "prop_type": "Lot Only",
    "tct_cct_no": "097-2024002768",
    "lot_area": "352",
    "floor_area": "0",
    "min_sellprice": 915200,
    "city_muni": "ROXAS CITY",
    "status": "1",
    "bid_acceptance_start": "2025-06-09T00:00:00",
    "bid_acceptance_end": "2025-06-13T23:59:00",
    "opening_of_offers": "2025-06-19T09:00:00"
  }
}
```

### Example 3: Get market statistics

```bash
curl "https://api.example.com/properties/stats"
```

**Response:**
```json
{
  "total_count": 1234,
  "avg_price": 850000.50,
  "min_price": 100000,
  "max_price": 5000000,
  "by_city": {
    "ROXAS CITY": 45,
    "MANILA": 150,
    "QUEZON CITY": 120
  },
  "by_type": {
    "Lot Only": 500,
    "House and Lot": 400,
    "Row House": 200,
    "Condominium": 134
  },
  "by_discount": {
    "Properties with no discount (1st auction)": 800,
    "Properties up to 30% discount (2nd auction)": 300,
    "Properties up to 45% discount (Negotiated Sale)": 134
  }
}
```

### Example 4: Paginated search with filters

```bash
# First page
curl "https://api.example.com/properties?city=MANILA&min_price=1000000&limit=20"

# Response includes last_key for next page
{
  "items": [...],
  "count": 20,
  "has_more": true,
  "last_key": "eyJzb3VyY2VfcHJvcGVydHlfaWQiOiAicGFnaWJpZ184NTgyMDIzMDkyODAwMjAifQ=="
}

# Next page
curl "https://api.example.com/properties?city=MANILA&min_price=1000000&limit=20&last_key=eyJzb3VyY2VfcHJvcGVydHlfaWQiOiAicGFnaWJpZ184NTgyMDIzMDkyODAwMjAifQ=="
```

## Performance Considerations

1. **Pagination**: Always use pagination for large result sets to avoid timeouts
2. **Filtering**: Apply filters to reduce the amount of data scanned
3. **Caching**: Consider caching frequently accessed data
4. **Indexing**: For production, consider adding GSIs for commonly filtered fields

## CORS Support

The API includes CORS headers to allow cross-origin requests from web applications:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token
```

## Lambda Deployment

The API is designed to run as an AWS Lambda function behind API Gateway.

### Environment Variables for Lambda
- `TABLE_NAME` - DynamoDB table name
- `AWS_REGION` - AWS region
- `CORS_ORIGIN` - Allowed CORS origin

### IAM Permissions Required
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/properties"
    }
  ]
}
```

## Troubleshooting

### No results returned
- Check if data exists in DynamoDB table
- Verify filters are not too restrictive
- Check AWS credentials and permissions

### Timeout errors
- Reduce the `limit` parameter
- Add more specific filters to reduce scan size
- Consider adding GSIs for better query performance

### CORS errors
- Verify `CORS_ORIGIN` environment variable
- Check API Gateway CORS configuration
- Ensure preflight OPTIONS requests are handled

## Future Enhancements

- [ ] Add Global Secondary Indexes for better query performance
- [ ] Implement caching layer (ElastiCache/CloudFront)
- [ ] Add full-text search capabilities
- [ ] Implement rate limiting
- [ ] Add authentication/authorization
- [ ] Create OpenAPI/Swagger specification
- [ ] Add request/response validation schemas