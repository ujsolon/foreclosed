# API Lambda Implementation Plan

## Overview
Implement a comprehensive REST API for querying foreclosed properties from DynamoDB with support for multiple filters, sorting, and pagination.

## API Endpoints Design

### 1. GET /properties
**Purpose**: List all properties with optional filters and pagination

**Query Parameters**:
- `city` - Filter by city/municipality (case-insensitive partial match)
- `prop_type` - Filter by property type (exact match)
- `branch` - Filter by branch name (case-insensitive partial match)
- `discount` - Filter by discount level (exact match)
- `min_price` - Minimum selling price (inclusive)
- `max_price` - Maximum selling price (inclusive)
- `status` - Filter by status (default: "1" for active)
- `sort_by` - Sort field (default: "min_sellprice")
- `sort_order` - Sort direction: "asc" or "desc" (default: "asc")
- `limit` - Number of results per page (default: 50, max: 100)
- `last_key` - Pagination token (base64 encoded)

**Response**:
```json
{
  "items": [...],
  "count": 50,
  "last_key": "base64_encoded_key",
  "has_more": true
}
```

### 2. GET /properties/{id}
**Purpose**: Get a single property by source_property_id

**Response**:
```json
{
  "item": {...}
}
```

### 3. GET /properties/stats
**Purpose**: Get aggregated statistics

**Response**:
```json
{
  "total_count": 1234,
  "avg_price": 850000,
  "min_price": 100000,
  "max_price": 5000000,
  "by_city": {...},
  "by_type": {...},
  "by_discount": {...}
}
```

## Implementation Details

### File Structure
```
backend/api/
├── lambda_function.py    # Lambda entry point
├── main.py              # API logic and handlers
├── requirements.txt     # Dependencies
└── utils.py            # Helper functions
```

### Key Components

#### 1. Request Router
- Parse API Gateway event
- Route to appropriate handler based on HTTP method and path
- Handle CORS headers

#### 2. Query Builder
- Build DynamoDB Scan with FilterExpression
- Handle multiple filter conditions
- Support pagination with ExclusiveStartKey

#### 3. Response Formatter
- Standardize response structure
- Handle Decimal to float conversion
- Base64 encode pagination tokens

#### 4. Error Handler
- Catch and format exceptions
- Return appropriate HTTP status codes
- Log errors for debugging

### DynamoDB Query Strategy

Since the table only has `source_property_id` as the hash key with no GSIs, we'll use:
- **Scan** with FilterExpression for list queries
- **GetItem** for single property retrieval
- Client-side sorting and filtering for complex queries

### Error Handling

1. **Validation Errors** (400)
   - Invalid query parameters
   - Invalid property ID format
   - Invalid pagination token

2. **Not Found** (404)
   - Property ID doesn't exist

3. **Server Errors** (500)
   - DynamoDB errors
   - Unexpected exceptions

### Performance Considerations

1. **Pagination**: Limit scan results to prevent timeouts
2. **Caching**: Add response headers for CloudFront caching
3. **Filtering**: Apply filters in DynamoDB when possible
4. **Sorting**: Use DynamoDB sort when available, otherwise client-side

## Testing Strategy

### Unit Tests
- Test each filter independently
- Test filter combinations
- Test pagination logic
- Test error handling

### Integration Tests
- Test with local DynamoDB
- Test with sample data
- Test edge cases (empty results, invalid params)

### Test Script
Create `backend/api/test_api.py` that:
1. Loads sample data into local DynamoDB
2. Tests all endpoints
3. Validates responses
4. Reports results

## Dependencies

```txt
boto3>=1.28.0
```

## Environment Variables

- `TABLE_NAME` - DynamoDB table name (default: "properties")
- `AWS_REGION` - AWS region (default: "us-east-1")
- `CORS_ORIGIN` - Allowed CORS origin (default: "*")

## Next Steps

1. ✅ Create implementation plan
2. Switch to Code mode
3. Implement `backend/api/main.py`
4. Implement `backend/api/utils.py`
5. Update `backend/api/lambda_function.py`
6. Create `backend/api/requirements.txt`
7. Update DynamoDB IAM policy
8. Create test script
9. Test locally
10. Document API usage