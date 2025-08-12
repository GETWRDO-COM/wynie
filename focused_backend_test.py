#!/usr/bin/env python3
"""
Focused Backend API Tests for Review Request
Tests specific endpoints as requested in the review
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class FocusedBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def test_auth_endpoints(self):
        """Test Auth endpoints (critical fix verification)"""
        try:
            # Test login with provided credentials - first time should auto-create
            login_data = {
                "email": "beetge@mwebbiz.co.za",
                "password": "Albee1990!"
            }
            
            print(f"Testing login to: {API_BASE}/auth/login")
            login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if login_response.status_code != 200:
                self.log_test("Auth Login", False, f"Login failed: HTTP {login_response.status_code}: {login_response.text}")
                return False
            
            login_result = login_response.json()
            
            # Validate login response structure
            required_fields = ['access_token', 'token_type', 'user']
            missing_fields = [field for field in required_fields if field not in login_result]
            if missing_fields:
                self.log_test("Auth Login", False, f"Login response missing fields: {missing_fields}")
                return False
            
            # Store auth token for subsequent requests
            self.auth_token = login_result['access_token']
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            self.log_test("Auth Login", True, f"Login successful, token obtained. User: {login_result['user']['email']}")
            
            # Test /auth/me endpoint
            me_response = self.session.get(f"{API_BASE}/auth/me", headers=auth_headers)
            if me_response.status_code != 200:
                self.log_test("Auth Me", False, f"Get current user failed: HTTP {me_response.status_code}")
                return False
            
            user_info = me_response.json()
            if user_info.get('email') != login_data['email']:
                self.log_test("Auth Me", False, f"User email mismatch: {user_info.get('email')} != {login_data['email']}")
                return False
            
            self.log_test("Auth Me", True, f"User info retrieved successfully: {user_info['email']}")
            
            # Test forgot password endpoint
            forgot_data = {"email": "beetge@mwebbiz.co.za"}
            forgot_response = self.session.post(f"{API_BASE}/auth/forgot-password", json=forgot_data)
            if forgot_response.status_code != 200:
                self.log_test("Auth Forgot Password", False, f"Forgot password failed: HTTP {forgot_response.status_code}")
                return False
            
            forgot_result = forgot_response.json()
            if 'message' not in forgot_result:
                self.log_test("Auth Forgot Password", False, "Forgot password response missing message")
                return False
            
            self.log_test("Auth Forgot Password", True, f"Generic success message returned: {forgot_result['message']}")
            return True
            
        except Exception as e:
            self.log_test("Auth Endpoints", False, f"Error: {str(e)}")
            return False

    def test_news_endpoint(self):
        """Test News endpoint"""
        try:
            # Test news with Stock Market category
            news_response = self.session.get(f"{API_BASE}/news?category=Stock%20Market")
            if news_response.status_code != 200:
                self.log_test("News Stock Market", False, f"News failed: HTTP {news_response.status_code}: {news_response.text}")
                return False
            
            news_data = news_response.json()
            
            # Validate response structure
            if 'items' not in news_data:
                self.log_test("News Stock Market", False, "News response missing 'items' field")
                return False
            
            items = news_data['items']
            if not items:
                self.log_test("News Stock Market", False, "No news items returned")
                return False
            
            # Validate item structure
            sample_item = items[0]
            required_fields = ['title', 'link']
            missing_fields = [field for field in required_fields if field not in sample_item]
            if missing_fields:
                self.log_test("News Stock Market", False, f"News item missing required fields: {missing_fields}")
                return False
            
            # Check optional fields
            optional_fields = ['published', 'thumb']
            present_optional = [field for field in optional_fields if field in sample_item]
            
            self.log_test("News Stock Market", True, f"News items returned: {len(items)}, required fields present, optional fields: {present_optional}")
            return True
            
        except Exception as e:
            self.log_test("News Stock Market", False, f"Error: {str(e)}")
            return False

    def test_greed_fear_endpoint(self):
        """Test Greed Fear endpoint"""
        try:
            greed_response = self.session.get(f"{API_BASE}/greed-fear")
            if greed_response.status_code != 200:
                self.log_test("Greed Fear", False, f"Greed Fear failed: HTTP {greed_response.status_code}: {greed_response.text}")
                return False
            
            greed_data = greed_response.json()
            
            # Validate required fields
            required_fields = ['now', 'last_updated']
            missing_fields = [field for field in required_fields if field not in greed_data]
            if missing_fields:
                self.log_test("Greed Fear", False, f"Greed Fear response missing fields: {missing_fields}")
                return False
            
            # Validate 'now' is in 0-100 range
            now_value = greed_data['now']
            if not isinstance(now_value, (int, float)) or not (0 <= now_value <= 100):
                self.log_test("Greed Fear", False, f"'now' value not in 0-100 range: {now_value}")
                return False
            
            self.log_test("Greed Fear", True, f"Shape correct, now={now_value} (0-100 range), last_updated present")
            return True
            
        except Exception as e:
            self.log_test("Greed Fear", False, f"Error: {str(e)}")
            return False

    def test_market_aggregates_endpoint(self):
        """Test Market Aggregates endpoint"""
        try:
            # Test default aggregates
            default_response = self.session.get(f"{API_BASE}/market/aggregates")
            if default_response.status_code != 200:
                self.log_test("Market Aggregates Default", False, f"Default aggregates failed: HTTP {default_response.status_code}: {default_response.text}")
                return False
            
            default_data = default_response.json()
            
            # Validate response structure
            required_fields = ['range', 'last_updated', 'data']
            missing_fields = [field for field in required_fields if field not in default_data]
            if missing_fields:
                self.log_test("Market Aggregates Default", False, f"Response missing fields: {missing_fields}")
                return False
            
            # Check for required tickers
            data = default_data['data']
            required_tickers = ['SPY', 'QQQ', 'I:DJI', 'TQQQ', 'SQQQ']
            missing_tickers = [ticker for ticker in required_tickers if ticker not in data]
            if missing_tickers:
                self.log_test("Market Aggregates Default", False, f"Missing tickers: {missing_tickers}")
                return False
            
            # Validate ticker data structure
            for ticker in required_tickers:
                ticker_data = data[ticker]
                ticker_required_fields = ['series', 'close', 'prev_close', 'change_pct']
                ticker_missing_fields = [field for field in ticker_required_fields if field not in ticker_data]
                if ticker_missing_fields:
                    self.log_test("Market Aggregates Default", False, f"{ticker} missing fields: {ticker_missing_fields}")
                    return False
            
            self.log_test("Market Aggregates Default", True, f"All 5 tickers present with numeric fields populated")
            
            # Test with range=1D
            range_response = self.session.get(f"{API_BASE}/market/aggregates?range=1D")
            if range_response.status_code != 200:
                self.log_test("Market Aggregates 1D", False, f"1D range failed: HTTP {range_response.status_code}: {range_response.text}")
                return False
            
            range_data = range_response.json()
            if range_data['range'] != '1D':
                self.log_test("Market Aggregates 1D", False, f"Range not set correctly: {range_data['range']}")
                return False
            
            # Verify I:DJI specifically works
            if 'I:DJI' not in range_data['data']:
                self.log_test("Market Aggregates 1D", False, "I:DJI not present in 1D data")
                return False
            
            self.log_test("Market Aggregates 1D", True, f"1D range working, I:DJI specifically confirmed")
            return True
            
        except Exception as e:
            self.log_test("Market Aggregates", False, f"Error: {str(e)}")
            return False

    def test_earnings_endpoint(self):
        """Test Earnings endpoint"""
        try:
            earnings_response = self.session.get(f"{API_BASE}/earnings")
            if earnings_response.status_code != 200:
                self.log_test("Earnings", False, f"Earnings failed: HTTP {earnings_response.status_code}: {earnings_response.text}")
                return False
            
            earnings_data = earnings_response.json()
            
            # Validate response structure
            required_fields = ['items', 'last_updated']
            missing_fields = [field for field in required_fields if field not in earnings_data]
            if missing_fields:
                self.log_test("Earnings", False, f"Earnings response missing fields: {missing_fields}")
                return False
            
            items = earnings_data['items']
            if items:
                # Validate item structure
                sample_item = items[0]
                item_required_fields = ['ticker', 'date']
                item_missing_fields = [field for field in item_required_fields if field not in sample_item]
                if item_missing_fields:
                    self.log_test("Earnings", False, f"Earnings item missing fields: {item_missing_fields}")
                    return False
            
            self.log_test("Earnings", True, f"Earnings endpoint working, {len(items)} items returned")
            return True
            
        except Exception as e:
            self.log_test("Earnings", False, f"Error: {str(e)}")
            return False

    def test_market_score_endpoint(self):
        """Test Market Score endpoint"""
        try:
            score_response = self.session.get(f"{API_BASE}/market-score")
            if score_response.status_code != 200:
                self.log_test("Market Score", False, f"Market Score failed: HTTP {score_response.status_code}: {score_response.text}")
                return False
            
            score_data = score_response.json()
            
            # Validate normalized fields
            required_fields = ['score', 'trend', 'last_updated', 'recommendation']
            missing_fields = [field for field in required_fields if field not in score_data]
            if missing_fields:
                self.log_test("Market Score", False, f"Market Score missing normalized fields: {missing_fields}")
                return False
            
            # Validate field types
            if not isinstance(score_data['score'], (int, float)):
                self.log_test("Market Score", False, f"Score not numeric: {score_data['score']}")
                return False
            
            if not isinstance(score_data['trend'], str):
                self.log_test("Market Score", False, f"Trend not string: {score_data['trend']}")
                return False
            
            self.log_test("Market Score", True, f"Normalized fields present: score={score_data['score']}, trend={score_data['trend']}")
            return True
            
        except Exception as e:
            self.log_test("Market Score", False, f"Error: {str(e)}")
            return False

    def test_polygon_key_endpoints(self):
        """Test Polygon key endpoints (auth required)"""
        try:
            if not self.auth_token:
                self.log_test("Polygon Key Endpoints", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test set Polygon key
            key_data = {"api_key": "dummy_test_key_12345"}
            set_key_response = self.session.post(f"{API_BASE}/integrations/polygon/key", json=key_data, headers=auth_headers)
            
            if set_key_response.status_code != 200:
                self.log_test("Polygon Set Key", False, f"Set key failed: HTTP {set_key_response.status_code}: {set_key_response.text}")
                return False
            
            set_key_result = set_key_response.json()
            if 'message' not in set_key_result:
                self.log_test("Polygon Set Key", False, "Set key response missing message")
                return False
            
            self.log_test("Polygon Set Key", True, f"Key saved successfully: {set_key_result['message']}")
            
            # Test get Polygon status
            status_response = self.session.get(f"{API_BASE}/integrations/polygon/status", headers=auth_headers)
            if status_response.status_code != 200:
                self.log_test("Polygon Status", False, f"Status failed: HTTP {status_response.status_code}: {status_response.text}")
                return False
            
            status_data = status_response.json()
            if not status_data.get('configured'):
                self.log_test("Polygon Status", False, f"Status not showing configured=true: {status_data}")
                return False
            
            self.log_test("Polygon Status", True, f"Status shows configured=true after setting key")
            return True
            
        except Exception as e:
            self.log_test("Polygon Key Endpoints", False, f"Error: {str(e)}")
            return False

    def run_focused_tests(self):
        """Run all focused tests"""
        print(f"🚀 Starting Focused Backend API Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        
        tests = [
            ("Auth Endpoints", self.test_auth_endpoints),
            ("News Stock Market", self.test_news_endpoint),
            ("Greed Fear", self.test_greed_fear_endpoint),
            ("Market Aggregates", self.test_market_aggregates_endpoint),
            ("Earnings", self.test_earnings_endpoint),
            ("Market Score", self.test_market_score_endpoint),
            ("Polygon Key Endpoints", self.test_polygon_key_endpoints),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                failed += 1
            print("-" * 40)
        
        print("=" * 60)
        print(f"📊 FOCUSED TEST RESULTS:")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {passed}/{passed+failed} ({(passed/(passed+failed)*100):.1f}%)")
        
        if failed == 0:
            print("🏆 ALL FOCUSED TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - see details above")
        
        return passed, failed

if __name__ == "__main__":
    tester = FocusedBackendTester()
    tester.run_focused_tests()