"""
Test script for Property API

This script tests the API Lambda function locally by simulating API Gateway events.
It can work with either local DynamoDB or AWS DynamoDB.

Usage:
    python test_api.py
"""
import json
import sys
import os
from decimal import Decimal

# Add parent directory to path to import lambda_function
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lambda_function import lambda_handler


class TestColors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print a formatted header"""
    print(f"\n{TestColors.HEADER}{TestColors.BOLD}{'='*60}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{text:^60}{TestColors.ENDC}")
    print(f"{TestColors.HEADER}{TestColors.BOLD}{'='*60}{TestColors.ENDC}\n")


def print_test(test_name):
    """Print test name"""
    print(f"{TestColors.OKCYAN}🧪 Testing: {test_name}{TestColors.ENDC}")


def print_success(message):
    """Print success message"""
    print(f"{TestColors.OKGREEN}✅ {message}{TestColors.ENDC}")


def print_error(message):
    """Print error message"""
    print(f"{TestColors.FAIL}❌ {message}{TestColors.ENDC}")


def print_warning(message):
    """Print warning message"""
    print(f"{TestColors.WARNING}⚠️  {message}{TestColors.ENDC}")


def create_api_event(method="GET", path="/properties", query_params=None, path_params=None):
    """
    Create a mock API Gateway event
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        query_params: Dictionary of query string parameters
        path_params: Dictionary of path parameters
        
    Returns:
        Mock API Gateway event dictionary
    """
    event = {
        "httpMethod": method,
        "path": path,
        "headers": {
            "Content-Type": "application/json"
        },
        "queryStringParameters": query_params,
        "pathParameters": path_params,
        "body": None,
        "isBase64Encoded": False
    }
    return event


def test_list_properties():
    """Test GET /properties - List all properties"""
    print_test("List all properties (default pagination)")
    
    event = create_api_event(path="/properties")
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    assert "items" in body, "Response should contain 'items'"
    assert "count" in body, "Response should contain 'count'"
    assert "has_more" in body, "Response should contain 'has_more'"
    
    print_success(f"Retrieved {body['count']} properties")
    print(f"   Has more: {body['has_more']}")
    print(f"   Scanned: {body.get('scanned_count', 'N/A')}")
    
    return body


def test_filter_by_city():
    """Test GET /properties?city=ROXAS"""
    print_test("Filter properties by city (ROXAS)")
    
    event = create_api_event(
        path="/properties",
        query_params={"city": "ROXAS", "limit": "10"}
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    print_success(f"Found {body['count']} properties in ROXAS")
    
    # Verify all items contain ROXAS in city_muni
    for item in body["items"]:
        city = item.get("city_muni", "")
        if "ROXAS" not in city.upper():
            print_warning(f"Item {item.get('source_property_id')} has city: {city}")
    
    return body


def test_filter_by_property_type():
    """Test GET /properties?prop_type=Lot Only"""
    print_test("Filter properties by type (Lot Only)")
    
    event = create_api_event(
        path="/properties",
        query_params={"prop_type": "Lot Only", "limit": "10"}
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    print_success(f"Found {body['count']} 'Lot Only' properties")
    
    return body


def test_filter_by_price_range():
    """Test GET /properties?min_price=500000&max_price=1000000"""
    print_test("Filter properties by price range (500k - 1M)")
    
    event = create_api_event(
        path="/properties",
        query_params={
            "min_price": "500000",
            "max_price": "1000000",
            "limit": "10"
        }
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    print_success(f"Found {body['count']} properties in price range")
    
    # Verify prices are within range
    for item in body["items"]:
        price = float(item.get("min_sellprice", 0))
        if not (500000 <= price <= 1000000):
            print_warning(f"Item {item.get('source_property_id')} has price: {price}")
    
    return body


def test_multiple_filters():
    """Test combining multiple filters"""
    print_test("Multiple filters (city + type + price)")
    
    event = create_api_event(
        path="/properties",
        query_params={
            "city": "ROXAS",
            "prop_type": "Lot Only",
            "min_price": "500000",
            "limit": "5"
        }
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    print_success(f"Found {body['count']} properties matching all filters")
    
    return body


def test_sorting():
    """Test sorting by price"""
    print_test("Sort by price (ascending)")
    
    event = create_api_event(
        path="/properties",
        query_params={
            "sort_by": "min_sellprice",
            "sort_order": "asc",
            "limit": "5"
        }
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    # Verify sorting
    prices = [float(item.get("min_sellprice", 0)) for item in body["items"]]
    is_sorted = all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
    
    if is_sorted:
        print_success(f"Properties correctly sorted by price (asc)")
        print(f"   Price range: {min(prices)} - {max(prices)}")
    else:
        print_error("Properties not correctly sorted!")
    
    return body


def test_pagination():
    """Test pagination"""
    print_test("Pagination (fetch 2 pages)")
    
    # First page
    event = create_api_event(
        path="/properties",
        query_params={"limit": "3"}
    )
    response = lambda_handler(event, None)
    body1 = json.loads(response["body"])
    
    print(f"   Page 1: {body1['count']} items")
    
    if body1.get("has_more") and body1.get("last_key"):
        # Second page
        event = create_api_event(
            path="/properties",
            query_params={
                "limit": "3",
                "last_key": body1["last_key"]
            }
        )
        response = lambda_handler(event, None)
        body2 = json.loads(response["body"])
        
        print(f"   Page 2: {body2['count']} items")
        
        # Verify no duplicate IDs
        ids1 = {item["source_property_id"] for item in body1["items"]}
        ids2 = {item["source_property_id"] for item in body2["items"]}
        overlap = ids1 & ids2
        
        if not overlap:
            print_success("Pagination working correctly (no duplicates)")
        else:
            print_error(f"Found {len(overlap)} duplicate items across pages!")
    else:
        print_warning("Not enough data to test pagination")
    
    return body1


def test_get_property_by_id():
    """Test GET /properties/{id}"""
    print_test("Get property by ID")
    
    # First, get a property ID from the list
    event = create_api_event(path="/properties", query_params={"limit": "1"})
    response = lambda_handler(event, None)
    list_body = json.loads(response["body"])
    
    if list_body.get("items"):
        property_id = list_body["items"][0]["source_property_id"]
        print(f"   Testing with ID: {property_id}")
        
        # Now get that specific property
        event = create_api_event(
            path=f"/properties/{property_id}",
            path_params={"id": property_id}
        )
        response = lambda_handler(event, None)
        
        assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
        body = json.loads(response["body"])
        
        assert "item" in body, "Response should contain 'item'"
        assert body["item"]["source_property_id"] == property_id
        
        print_success(f"Retrieved property: {property_id}")
        print(f"   Location: {body['item'].get('prop_location', 'N/A')}")
        print(f"   Price: {body['item'].get('min_sellprice', 'N/A')}")
        
        return body
    else:
        print_warning("No properties available to test")
        return None


def test_get_nonexistent_property():
    """Test GET /properties/{id} with non-existent ID"""
    print_test("Get non-existent property (should return 404)")
    
    event = create_api_event(
        path="/properties/nonexistent_id_12345",
        path_params={"id": "nonexistent_id_12345"}
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 404, f"Expected 404, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    assert "error" in body, "Error response should contain 'error'"
    print_success("Correctly returned 404 for non-existent property")
    
    return body


def test_statistics():
    """Test GET /properties/stats"""
    print_test("Get statistics")
    
    event = create_api_event(path="/properties/stats")
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = json.loads(response["body"])
    
    assert "total_count" in body, "Stats should contain 'total_count'"
    
    print_success(f"Statistics retrieved successfully")
    print(f"   Total properties: {body.get('total_count', 0)}")
    print(f"   Average price: ₱{body.get('avg_price', 0):,.2f}")
    print(f"   Price range: ₱{body.get('min_price', 0):,.0f} - ₱{body.get('max_price', 0):,.0f}")
    
    if "by_city" in body:
        print(f"   Top cities: {list(body['by_city'].keys())[:3]}")
    
    return body


def test_invalid_parameters():
    """Test with invalid parameters"""
    print_test("Invalid parameters (should return 400)")
    
    # Invalid limit
    event = create_api_event(
        path="/properties",
        query_params={"limit": "999"}
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 400, f"Expected 400, got {response['statusCode']}"
    print_success("Correctly rejected invalid limit")
    
    # Invalid price
    event = create_api_event(
        path="/properties",
        query_params={"min_price": "not_a_number"}
    )
    response = lambda_handler(event, None)
    
    assert response["statusCode"] == 400, f"Expected 400, got {response['statusCode']}"
    print_success("Correctly rejected invalid price")
    
    return True


def test_cors_headers():
    """Test CORS headers are present"""
    print_test("CORS headers")
    
    event = create_api_event(path="/properties")
    response = lambda_handler(event, None)
    
    headers = response.get("headers", {})
    
    assert "Access-Control-Allow-Origin" in headers, "Missing CORS origin header"
    assert "Access-Control-Allow-Methods" in headers, "Missing CORS methods header"
    
    print_success("CORS headers present")
    print(f"   Origin: {headers.get('Access-Control-Allow-Origin')}")
    
    return True


def run_all_tests():
    """Run all test cases"""
    print_header("Property API Test Suite")
    
    tests = [
        ("List Properties", test_list_properties),
        ("Filter by City", test_filter_by_city),
        ("Filter by Property Type", test_filter_by_property_type),
        ("Filter by Price Range", test_filter_by_price_range),
        ("Multiple Filters", test_multiple_filters),
        ("Sorting", test_sorting),
        ("Pagination", test_pagination),
        ("Get Property by ID", test_get_property_by_id),
        ("Get Non-existent Property", test_get_nonexistent_property),
        ("Statistics", test_statistics),
        ("Invalid Parameters", test_invalid_parameters),
        ("CORS Headers", test_cors_headers),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except AssertionError as e:
            print_error(f"Test failed: {e}")
            failed += 1
            print()
        except Exception as e:
            print_error(f"Test error: {e}")
            failed += 1
            print()
    
    # Print summary
    print_header("Test Summary")
    total = passed + failed
    print(f"Total tests: {total}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print_success("All tests passed! 🎉")
    
    return failed == 0


if __name__ == "__main__":
    print(f"\n{TestColors.BOLD}Property API Test Script{TestColors.ENDC}")
    print(f"Testing against table: {os.environ.get('TABLE_NAME', 'properties')}")
    print(f"Region: {os.environ.get('AWS_REGION', 'us-east-1')}\n")
    
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
