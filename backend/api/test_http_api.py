"""
HTTP API Test Script

Tests the Property API via HTTP requests.
Works with both local server and AWS deployment.

Usage:
    # Test local server
    python test_http_api.py
    
    # Test AWS deployment
    python test_http_api.py --url https://your-api.execute-api.us-east-1.amazonaws.com
    
    # Verbose output
    python test_http_api.py --verbose
"""
import requests
import sys
import argparse
from typing import Optional
import json


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


class APITester:
    """Test the Property API via HTTP requests"""
    
    def __init__(self, base_url: str, verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{TestColors.HEADER}{TestColors.BOLD}{'='*60}{TestColors.ENDC}")
        print(f"{TestColors.HEADER}{TestColors.BOLD}{text:^60}{TestColors.ENDC}")
        print(f"{TestColors.HEADER}{TestColors.BOLD}{'='*60}{TestColors.ENDC}\n")
    
    def print_test(self, test_name):
        """Print test name"""
        print(f"{TestColors.OKCYAN}🧪 Testing: {test_name}{TestColors.ENDC}")
    
    def print_success(self, message):
        """Print success message"""
        print(f"{TestColors.OKGREEN}✅ {message}{TestColors.ENDC}")
        self.passed += 1
    
    def print_error(self, message):
        """Print error message"""
        print(f"{TestColors.FAIL}❌ {message}{TestColors.ENDC}")
        self.failed += 1
    
    def print_warning(self, message):
        """Print warning message"""
        print(f"{TestColors.WARNING}⚠️  {message}{TestColors.ENDC}")
    
    def print_verbose(self, message):
        """Print verbose message"""
        if self.verbose:
            print(f"   {message}")
    
    def make_request(self, method: str, endpoint: str, params: Optional[dict] = None):
        """Make HTTP request and return response"""
        url = f"{self.base_url}{endpoint}"
        self.print_verbose(f"Request: {method} {url}")
        if params:
            self.print_verbose(f"Params: {params}")
        
        try:
            response = requests.request(method, url, params=params, timeout=30)
            self.print_verbose(f"Status: {response.status_code}")
            
            # Print response body for debugging if not 2xx
            if response.status_code >= 400:
                try:
                    error_body = response.json()
                    self.print_verbose(f"Error response: {json.dumps(error_body, indent=2)}")
                except:
                    self.print_verbose(f"Error response (raw): {response.text[:200]}")
            
            return response
        except requests.exceptions.Timeout:
            self.print_error(f"Request timed out after 30 seconds")
            self.print_verbose(f"URL: {url}")
            return None
        except requests.exceptions.ConnectionError as e:
            self.print_error(f"Connection error: {e}")
            self.print_verbose(f"URL: {url}")
            self.print_warning("Is the server running? Try: python local_server.py")
            return None
        except requests.exceptions.RequestException as e:
            self.print_error(f"Request failed: {e}")
            self.print_verbose(f"URL: {url}")
            return None
        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            self.print_verbose(f"URL: {url}")
            import traceback
            self.print_verbose(traceback.format_exc())
            return None
    
    def test_list_properties(self):
        """Test GET /properties - List all properties"""
        self.print_test("List all properties (default pagination)")
        
        response = self.make_request("GET", "/properties")
        
        if not response:
            self.print_error("Request failed")
            return
        
        if response.status_code != 200:
            self.print_error(f"Expected 200, got {response.status_code}")
            return
        
        try:
            data = response.json()
            assert "items" in data, "Response should contain 'items'"
            assert "count" in data, "Response should contain 'count'"
            assert "has_more" in data, "Response should contain 'has_more'"
            
            self.print_success(f"Retrieved {data['count']} properties")
            self.print_verbose(f"Has more: {data['has_more']}")
            self.print_verbose(f"Scanned: {data.get('scanned_count', 'N/A')}")
            
            return data
        except (json.JSONDecodeError, AssertionError) as e:
            self.print_error(f"Response validation failed: {e}")
    
    def test_filter_by_city(self):
        """Test GET /properties?city=ROXAS"""
        self.print_test("Filter properties by city (ROXAS)")
        
        response = self.make_request("GET", "/properties", params={"city": "ROXAS", "limit": "10"})
        
        if not response or response.status_code != 200:
            self.print_error(f"Request failed with status {response.status_code if response else 'N/A'}")
            return
        
        try:
            data = response.json()
            self.print_success(f"Found {data['count']} properties in ROXAS")
            
            # Verify filtering worked
            for item in data["items"]:
                city = item.get("city_muni", "")
                if "ROXAS" not in city.upper():
                    self.print_warning(f"Item {item.get('source_property_id')} has city: {city}")
            
            return data
        except (json.JSONDecodeError, KeyError) as e:
            self.print_error(f"Response parsing failed: {e}")
    
    def test_filter_by_property_type(self):
        """Test GET /properties?prop_type=Lot Only"""
        self.print_test("Filter properties by type (Lot Only)")
        
        response = self.make_request("GET", "/properties", params={"prop_type": "Lot Only", "limit": "10"})
        
        if not response or response.status_code != 200:
            self.print_error(f"Request failed")
            return
        
        try:
            data = response.json()
            self.print_success(f"Found {data['count']} 'Lot Only' properties")
            return data
        except (json.JSONDecodeError, KeyError) as e:
            self.print_error(f"Response parsing failed: {e}")
    
    def test_filter_by_price_range(self):
        """Test GET /properties?min_price=500000&max_price=1000000"""
        self.print_test("Filter properties by price range (500k - 1M)")
        
        response = self.make_request("GET", "/properties", params={
            "min_price": "500000",
            "max_price": "1000000",
            "limit": "10"
        })
        
        if not response or response.status_code != 200:
            self.print_error(f"Request failed")
            return
        
        try:
            data = response.json()
            self.print_success(f"Found {data['count']} properties in price range")
            
            # Verify prices are within range
            for item in data["items"]:
                price = float(item.get("min_sellprice", 0))
                if not (500000 <= price <= 1000000):
                    self.print_warning(f"Item {item.get('source_property_id')} has price: {price}")
            
            return data
        except (json.JSONDecodeError, KeyError) as e:
            self.print_error(f"Response parsing failed: {e}")
    
    def test_multiple_filters(self):
        """Test combining multiple filters"""
        self.print_test("Multiple filters (city + type + price)")
        
        response = self.make_request("GET", "/properties", params={
            "city": "ROXAS",
            "prop_type": "Lot Only",
            "min_price": "500000",
            "limit": "5"
        })
        
        if not response or response.status_code != 200:
            self.print_error(f"Request failed")
            return
        
        try:
            data = response.json()
            self.print_success(f"Found {data['count']} properties matching all filters")
            return data
        except (json.JSONDecodeError, KeyError) as e:
            self.print_error(f"Response parsing failed: {e}")
    
    def test_sorting(self):
        """Test sorting by price"""
        self.print_test("Sort by price (ascending)")
        
        response = self.make_request("GET", "/properties", params={
            "sort_by": "min_sellprice",
            "sort_order": "asc",
            "limit": "5"
        })
        
        if not response or response.status_code != 200:
            self.print_error(f"Request failed")
            return
        
        try:
            data = response.json()
            
            # Verify sorting
            prices = [float(item.get("min_sellprice", 0)) for item in data["items"]]
            is_sorted = all(prices[i] <= prices[i+1] for i in range(len(prices)-1))
            
            if is_sorted and prices:
                self.print_success(f"Properties correctly sorted by price (asc)")
                self.print_verbose(f"Price range: {min(prices)} - {max(prices)}")
            elif not prices:
                self.print_warning("No properties to verify sorting")
            else:
                self.print_error("Properties not correctly sorted!")
            
            return data
        except (json.JSONDecodeError, KeyError) as e:
            self.print_error(f"Response parsing failed: {e}")
    
    def test_pagination(self):
        """Test pagination"""
        self.print_test("Pagination (fetch 2 pages)")
        
        # First page
        response = self.make_request("GET", "/properties", params={"limit": "3"})
        
        if not response or response.status_code != 200:
            self.print_error(f"Request failed")
            return
        
        try:
            data1 = response.json()
            self.print_verbose(f"Page 1: {data1['count']} items")
            
            if data1.get("has_more") and data1.get("last_key"):
                # Second page
                response = self.make_request("GET", "/properties", params={
                    "limit": "3",
                    "last_key": data1["last_key"]
                })
                
                if response and response.status_code == 200:
                    data2 = response.json()
                    self.print_verbose(f"Page 2: {data2['count']} items")
                    
                    # Verify no duplicate IDs
                    ids1 = {item["source_property_id"] for item in data1["items"]}
                    ids2 = {item["source_property_id"] for item in data2["items"]}
                    overlap = ids1 & ids2
                    
                    if not overlap:
                        self.print_success("Pagination working correctly (no duplicates)")
                    else:
                        self.print_error(f"Found {len(overlap)} duplicate items across pages!")
                else:
                    self.print_error("Failed to fetch second page")
            else:
                self.print_warning("Not enough data to test pagination")
            
            return data1
        except (json.JSONDecodeError, KeyError) as e:
            self.print_error(f"Response parsing failed: {e}")
    
    def test_get_property_by_id(self):
        """Test GET /properties/{id}"""
        self.print_test("Get property by ID")
        
        # First, get a property ID from the list
        response = self.make_request("GET", "/properties", params={"limit": "1"})
        
        if not response or response.status_code != 200:
            self.print_error("Failed to get property list")
            return
        
        try:
            data = response.json()
            
            if data["items"]:
                property_id = data["items"][0]["source_property_id"]
                self.print_verbose(f"Testing with ID: {property_id}")
                
                # Now get that specific property
                response = self.make_request("GET", f"/properties/{property_id}")
                
                if not response or response.status_code != 200:
                    self.print_error(f"Failed to get property {property_id}")
                    return
                
                prop_data = response.json()
                
                assert "item" in prop_data, "Response should contain 'item'"
                assert prop_data["item"]["source_property_id"] == property_id
                
                self.print_success(f"Retrieved property: {property_id}")
                self.print_verbose(f"Location: {prop_data['item'].get('prop_location', 'N/A')}")
                self.print_verbose(f"Price: {prop_data['item'].get('min_sellprice', 'N/A')}")
                
                return prop_data
            else:
                self.print_warning("No properties available to test")
        except (json.JSONDecodeError, KeyError, AssertionError) as e:
            self.print_error(f"Test failed: {e}")
    
    def test_get_nonexistent_property(self):
        """Test GET /properties/{id} with non-existent ID"""
        self.print_test("Get non-existent property (should return 404)")
        
        response = self.make_request("GET", "/properties/nonexistent_id_12345")
        
        if response is None:
            self.print_error("Request failed")
            return
        
        if response.status_code == 404:
            try:
                data = response.json()
                assert "error" in data, "Error response should contain 'error'"
                self.print_success("Correctly returned 404 for non-existent property")
            except (json.JSONDecodeError, AssertionError) as e:
                self.print_error(f"Response validation failed: {e}")
        else:
            self.print_error(f"Expected 404, got {response.status_code}")
    
    def test_statistics(self):
        """Test GET /properties/stats"""
        self.print_test("Get statistics")
        
        response = self.make_request("GET", "/properties/stats")
        
        if not response or response.status_code != 200:
            self.print_error(f"Request failed")
            return
        
        try:
            data = response.json()
            
            assert "total_count" in data, "Stats should contain 'total_count'"
            
            self.print_success(f"Statistics retrieved successfully")
            self.print_verbose(f"Total properties: {data.get('total_count', 0)}")
            self.print_verbose(f"Average price: ₱{data.get('avg_price', 0):,.2f}")
            self.print_verbose(f"Price range: ₱{data.get('min_price', 0):,.0f} - ₱{data.get('max_price', 0):,.0f}")
            
            if "by_city" in data:
                top_cities = list(data['by_city'].keys())[:3]
                self.print_verbose(f"Top cities: {top_cities}")
            
            return data
        except (json.JSONDecodeError, KeyError, AssertionError) as e:
            self.print_error(f"Response validation failed: {e}")
    
    def test_invalid_parameters(self):
        """Test with invalid parameters"""
        self.print_test("Invalid parameters (should return 400)")
        
        # Invalid limit
        response = self.make_request("GET", "/properties", params={"limit": "999"})
        
        if response is None:
            self.print_error("Request failed - server may not be running or connection error")
            self.print_verbose("Check if local_server.py is running")
            return
        
        self.print_verbose(f"Response status: {response.status_code}")
        
        if response.status_code == 400:
            self.print_success("Correctly rejected invalid limit")
            try:
                error_data = response.json()
                self.print_verbose(f"Error message: {error_data.get('error', 'N/A')}")
            except:
                pass
        else:
            self.print_error(f"Expected 400, got {response.status_code}")
            try:
                self.print_verbose(f"Response: {response.text[:200]}")
            except:
                pass
        
        # Invalid price
        response = self.make_request("GET", "/properties", params={"min_price": "not_a_number"})
        
        if response is None:
            self.print_error("Request failed - server may not be running")
            return
        
        if response.status_code == 400:
            self.print_success("Correctly rejected invalid price")
        else:
            self.print_error(f"Expected 400, got {response.status_code}")
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        self.print_test("CORS headers")
        
        response = self.make_request("GET", "/properties")
        
        if not response:
            self.print_error("Request failed")
            return
        
        headers = response.headers
        
        if "Access-Control-Allow-Origin" in headers:
            self.print_success("CORS headers present")
            self.print_verbose(f"Origin: {headers.get('Access-Control-Allow-Origin')}")
        else:
            self.print_warning("CORS headers not found (may be OK for local testing)")
    
    def run_all_tests(self):
        """Run all test cases"""
        self.print_header("Property API HTTP Test Suite")
        
        print(f"Testing API at: {TestColors.BOLD}{self.base_url}{TestColors.ENDC}\n")
        
        tests = [
            ("List Properties", self.test_list_properties),
            ("Filter by City", self.test_filter_by_city),
            ("Filter by Property Type", self.test_filter_by_property_type),
            ("Filter by Price Range", self.test_filter_by_price_range),
            ("Multiple Filters", self.test_multiple_filters),
            ("Sorting", self.test_sorting),
            ("Pagination", self.test_pagination),
            ("Get Property by ID", self.test_get_property_by_id),
            ("Get Non-existent Property", self.test_get_nonexistent_property),
            ("Statistics", self.test_statistics),
            ("Invalid Parameters", self.test_invalid_parameters),
            ("CORS Headers", self.test_cors_headers),
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
                print()
            except Exception as e:
                self.print_error(f"Test error: {e}")
                print()
        
        # Print summary
        self.print_header("Test Summary")
        total = self.passed + self.failed
        print(f"Total tests: {total}")
        self.print_success(f"Passed: {self.passed}")
        if self.failed > 0:
            self.print_error(f"Failed: {self.failed}")
        else:
            self.print_success("All tests passed! 🎉")
        
        return self.failed == 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Test Property API via HTTP")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    print(f"\n{TestColors.BOLD}Property API HTTP Test Script{TestColors.ENDC}")
    print(f"Testing against: {args.url}\n")
    
    # Check if server is reachable
    try:
        response = requests.get(args.url, timeout=5)
        print(f"{TestColors.OKGREEN}✅ Server is reachable{TestColors.ENDC}\n")
    except requests.exceptions.RequestException as e:
        print(f"{TestColors.FAIL}❌ Cannot reach server at {args.url}{TestColors.ENDC}")
        print(f"{TestColors.FAIL}   Error: {e}{TestColors.ENDC}")
        print(f"\n{TestColors.WARNING}💡 Make sure the server is running:{TestColors.ENDC}")
        print(f"   python local_server.py\n")
        sys.exit(1)
    
    # Run tests
    tester = APITester(args.url, verbose=args.verbose)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob
