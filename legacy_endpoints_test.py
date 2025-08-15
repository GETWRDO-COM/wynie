#!/usr/bin/env python3
"""
Legacy Endpoints Backend Test for Review Request
Tests newly added legacy endpoints and verifies UI dependencies
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

class LegacyEndpointsTester:
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
        
    def test_auth_login(self):
        """Test POST /api/auth/login -> obtain token"""
        try:
            login_data = {
                "email": "beetge@mwebbiz.co.za",
                "password": "Albee1990!"
            }
            
            print(f"Testing login to: {API_BASE}/auth/login")
            login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if login_response.status_code != 200:
                self.log_test("POST /api/auth/login", False, f"HTTP {login_response.status_code}: {login_response.text}")
                return False
            
            login_result = login_response.json()
            
            # Validate login response structure
            required_fields = ['access_token', 'token_type', 'user']
            missing_fields = [field for field in required_fields if field not in login_result]
            if missing_fields:
                self.log_test("POST /api/auth/login", False, f"Response missing fields: {missing_fields}")
                return False
            
            # Store auth token for subsequent requests
            self.auth_token = login_result['access_token']
            
            # Sample response for reporting
            sample_response = {
                "access_token": "JWT_TOKEN_RECEIVED",
                "token_type": login_result['token_type'],
                "user": login_result['user']
            }
            
            self.log_test("POST /api/auth/login", True, f"Login successful, token obtained", sample_response)
            return True
            
        except Exception as e:
            self.log_test("POST /api/auth/login", False, f"Error: {str(e)}")
            return False

    def test_dashboard_endpoint(self):
        """Test GET /api/dashboard -> 200 JSON with message ok"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/dashboard", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            dashboard_response = self.session.get(f"{API_BASE}/dashboard", headers=auth_headers)
            
            if dashboard_response.status_code != 200:
                self.log_test("GET /api/dashboard", False, f"HTTP {dashboard_response.status_code}: {dashboard_response.text}")
                return False
            
            dashboard_data = dashboard_response.json()
            
            # Check for message field
            if 'message' not in dashboard_data:
                self.log_test("GET /api/dashboard", False, "Response missing 'message' field")
                return False
            
            if dashboard_data['message'] != 'ok':
                self.log_test("GET /api/dashboard", False, f"Message not 'ok': {dashboard_data['message']}")
                return False
            
            self.log_test("GET /api/dashboard", True, f"200 JSON with message ok", dashboard_data)
            return True
            
        except Exception as e:
            self.log_test("GET /api/dashboard", False, f"Error: {str(e)}")
            return False

    def test_etfs_endpoint(self):
        """Test GET /api/etfs?limit=5 -> 200 JSON (array, may be empty)"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/etfs?limit=5", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            etfs_response = self.session.get(f"{API_BASE}/etfs?limit=5", headers=auth_headers)
            
            if etfs_response.status_code != 200:
                self.log_test("GET /api/etfs?limit=5", False, f"HTTP {etfs_response.status_code}: {etfs_response.text}")
                return False
            
            etfs_data = etfs_response.json()
            
            # Should be an array
            if not isinstance(etfs_data, list):
                self.log_test("GET /api/etfs?limit=5", False, f"Response not an array: {type(etfs_data)}")
                return False
            
            # Array may be empty, that's OK
            sample_response = etfs_data[:2] if len(etfs_data) > 2 else etfs_data  # Show first 2 items max
            
            self.log_test("GET /api/etfs?limit=5", True, f"200 JSON array with {len(etfs_data)} items", sample_response)
            return True
            
        except Exception as e:
            self.log_test("GET /api/etfs?limit=5", False, f"Error: {str(e)}")
            return False

    def test_etfs_sectors_endpoint(self):
        """Test GET /api/etfs/sectors -> 200 JSON with sectors array"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/etfs/sectors", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            sectors_response = self.session.get(f"{API_BASE}/etfs/sectors", headers=auth_headers)
            
            if sectors_response.status_code != 200:
                self.log_test("GET /api/etfs/sectors", False, f"HTTP {sectors_response.status_code}: {sectors_response.text}")
                return False
            
            sectors_data = sectors_response.json()
            
            # Should have sectors field
            if 'sectors' not in sectors_data:
                self.log_test("GET /api/etfs/sectors", False, "Response missing 'sectors' field")
                return False
            
            sectors = sectors_data['sectors']
            if not isinstance(sectors, list):
                self.log_test("GET /api/etfs/sectors", False, f"Sectors not an array: {type(sectors)}")
                return False
            
            self.log_test("GET /api/etfs/sectors", True, f"200 JSON with sectors array ({len(sectors)} sectors)", sectors_data)
            return True
            
        except Exception as e:
            self.log_test("GET /api/etfs/sectors", False, f"Error: {str(e)}")
            return False

    def test_swing_leaders_endpoint(self):
        """Test GET /api/etfs/swing-leaders -> 200 JSON (array, may be empty)"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/etfs/swing-leaders", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            leaders_response = self.session.get(f"{API_BASE}/etfs/swing-leaders", headers=auth_headers)
            
            if leaders_response.status_code != 200:
                self.log_test("GET /api/etfs/swing-leaders", False, f"HTTP {leaders_response.status_code}: {leaders_response.text}")
                return False
            
            leaders_data = leaders_response.json()
            
            # Should be an array
            if not isinstance(leaders_data, list):
                self.log_test("GET /api/etfs/swing-leaders", False, f"Response not an array: {type(leaders_data)}")
                return False
            
            # Array may be empty, that's OK
            sample_response = leaders_data[:2] if len(leaders_data) > 2 else leaders_data  # Show first 2 items max
            
            self.log_test("GET /api/etfs/swing-leaders", True, f"200 JSON array with {len(leaders_data)} items", sample_response)
            return True
            
        except Exception as e:
            self.log_test("GET /api/etfs/swing-leaders", False, f"Error: {str(e)}")
            return False

    def test_watchlists_custom_endpoint(self):
        """Test GET /api/watchlists/custom -> 200 JSON (array, may be empty)"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/watchlists/custom", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            watchlists_response = self.session.get(f"{API_BASE}/watchlists/custom", headers=auth_headers)
            
            if watchlists_response.status_code != 200:
                self.log_test("GET /api/watchlists/custom", False, f"HTTP {watchlists_response.status_code}: {watchlists_response.text}")
                return False
            
            watchlists_data = watchlists_response.json()
            
            # Should be an array
            if not isinstance(watchlists_data, list):
                self.log_test("GET /api/watchlists/custom", False, f"Response not an array: {type(watchlists_data)}")
                return False
            
            # Array may be empty, that's OK
            sample_response = watchlists_data[:2] if len(watchlists_data) > 2 else watchlists_data  # Show first 2 items max
            
            self.log_test("GET /api/watchlists/custom", True, f"200 JSON array with {len(watchlists_data)} items", sample_response)
            return True
            
        except Exception as e:
            self.log_test("GET /api/watchlists/custom", False, f"Error: {str(e)}")
            return False

    def test_charts_indices_endpoint(self):
        """Test GET /api/charts/indices?timeframe=1m -> 200 JSON with {data:{}}"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/charts/indices?timeframe=1m", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            charts_response = self.session.get(f"{API_BASE}/charts/indices?timeframe=1m", headers=auth_headers)
            
            if charts_response.status_code != 200:
                self.log_test("GET /api/charts/indices?timeframe=1m", False, f"HTTP {charts_response.status_code}: {charts_response.text}")
                return False
            
            charts_data = charts_response.json()
            
            # Should have data field
            if 'data' not in charts_data:
                self.log_test("GET /api/charts/indices?timeframe=1m", False, "Response missing 'data' field")
                return False
            
            data = charts_data['data']
            if not isinstance(data, dict):
                self.log_test("GET /api/charts/indices?timeframe=1m", False, f"Data not an object: {type(data)}")
                return False
            
            self.log_test("GET /api/charts/indices?timeframe=1m", True, f"200 JSON with data object", charts_data)
            return True
            
        except Exception as e:
            self.log_test("GET /api/charts/indices?timeframe=1m", False, f"Error: {str(e)}")
            return False

    def test_sanity_check_endpoints(self):
        """Sanity check previously tested endpoints"""
        sanity_tests = []
        
        # Test /api/news
        try:
            news_response = self.session.get(f"{API_BASE}/news?category=Stock%20Market")
            if news_response.status_code == 200:
                news_data = news_response.json()
                if 'items' in news_data and isinstance(news_data['items'], list):
                    sanity_tests.append(("GET /api/news", True, f"200 OK, {len(news_data['items'])} items"))
                else:
                    sanity_tests.append(("GET /api/news", False, "Invalid response structure"))
            else:
                sanity_tests.append(("GET /api/news", False, f"HTTP {news_response.status_code}"))
        except Exception as e:
            sanity_tests.append(("GET /api/news", False, f"Error: {str(e)}"))
        
        # Test /api/greed-fear
        try:
            greed_response = self.session.get(f"{API_BASE}/greed-fear")
            if greed_response.status_code == 200:
                greed_data = greed_response.json()
                if 'now' in greed_data and isinstance(greed_data['now'], (int, float)):
                    sanity_tests.append(("GET /api/greed-fear", True, f"200 OK, score={greed_data['now']}"))
                else:
                    sanity_tests.append(("GET /api/greed-fear", False, "Invalid response structure"))
            else:
                sanity_tests.append(("GET /api/greed-fear", False, f"HTTP {greed_response.status_code}"))
        except Exception as e:
            sanity_tests.append(("GET /api/greed-fear", False, f"Error: {str(e)}"))
        
        # Test /api/market/aggregates
        try:
            agg_response = self.session.get(f"{API_BASE}/market/aggregates")
            if agg_response.status_code == 200:
                agg_data = agg_response.json()
                if 'data' in agg_data and isinstance(agg_data['data'], dict):
                    tickers = list(agg_data['data'].keys())
                    sanity_tests.append(("GET /api/market/aggregates", True, f"200 OK, {len(tickers)} tickers"))
                else:
                    sanity_tests.append(("GET /api/market/aggregates", False, "Invalid response structure"))
            else:
                sanity_tests.append(("GET /api/market/aggregates", False, f"HTTP {agg_response.status_code}"))
        except Exception as e:
            sanity_tests.append(("GET /api/market/aggregates", False, f"Error: {str(e)}"))
        
        # Test /api/market-score
        try:
            score_response = self.session.get(f"{API_BASE}/market-score")
            if score_response.status_code == 200:
                score_data = score_response.json()
                if 'score' in score_data and isinstance(score_data['score'], (int, float)):
                    sanity_tests.append(("GET /api/market-score", True, f"200 OK, score={score_data['score']}"))
                else:
                    sanity_tests.append(("GET /api/market-score", False, "Invalid response structure"))
            else:
                sanity_tests.append(("GET /api/market-score", False, f"HTTP {score_response.status_code}"))
        except Exception as e:
            sanity_tests.append(("GET /api/market-score", False, f"Error: {str(e)}"))
        
        # Test /api/earnings
        try:
            earnings_response = self.session.get(f"{API_BASE}/earnings")
            if earnings_response.status_code == 200:
                earnings_data = earnings_response.json()
                if 'items' in earnings_data and isinstance(earnings_data['items'], list):
                    sanity_tests.append(("GET /api/earnings", True, f"200 OK, {len(earnings_data['items'])} items"))
                else:
                    sanity_tests.append(("GET /api/earnings", False, "Invalid response structure"))
            else:
                sanity_tests.append(("GET /api/earnings", False, f"HTTP {earnings_response.status_code}"))
        except Exception as e:
            sanity_tests.append(("GET /api/earnings", False, f"Error: {str(e)}"))
        
        # Log all sanity test results
        for test_name, success, details in sanity_tests:
            self.log_test(f"SANITY: {test_name}", success, details)
        
        # Return True if all sanity tests passed
        return all(success for _, success, _ in sanity_tests)

    def run_legacy_tests(self):
        """Run all legacy endpoint tests"""
        print(f"🚀 Starting Legacy Endpoints Backend Tests")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 80)
        
        # Step 1: Login and obtain token
        print("STEP 1: Authentication")
        print("-" * 40)
        if not self.test_auth_login():
            print("❌ Authentication failed - cannot proceed with bearer token tests")
            return
        
        print()
        print("STEP 2: Bearer Token Protected Endpoints")
        print("-" * 40)
        
        # Step 2: Test bearer token protected endpoints
        bearer_tests = [
            ("GET /api/dashboard", self.test_dashboard_endpoint),
            ("GET /api/etfs?limit=5", self.test_etfs_endpoint),
            ("GET /api/etfs/sectors", self.test_etfs_sectors_endpoint),
            ("GET /api/etfs/swing-leaders", self.test_swing_leaders_endpoint),
            ("GET /api/watchlists/custom", self.test_watchlists_custom_endpoint),
            ("GET /api/charts/indices?timeframe=1m", self.test_charts_indices_endpoint),
        ]
        
        bearer_passed = 0
        bearer_failed = 0
        
        for test_name, test_func in bearer_tests:
            try:
                if test_func():
                    bearer_passed += 1
                else:
                    bearer_failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                bearer_failed += 1
            print()
        
        print("STEP 3: Sanity Check Previously Tested Endpoints")
        print("-" * 40)
        
        # Step 3: Sanity check
        sanity_passed = self.test_sanity_check_endpoints()
        
        print()
        print("=" * 80)
        print(f"📊 LEGACY ENDPOINTS TEST RESULTS:")
        print(f"🔐 Authentication: {'✅ PASS' if self.auth_token else '❌ FAIL'}")
        print(f"🛡️  Bearer Token Tests: ✅ {bearer_passed} passed, ❌ {bearer_failed} failed")
        print(f"🔍 Sanity Check: {'✅ PASS' if sanity_passed else '❌ FAIL'}")
        
        total_tests = 1 + len(bearer_tests) + 5  # 1 auth + 6 bearer + 5 sanity
        total_passed = (1 if self.auth_token else 0) + bearer_passed + (5 if sanity_passed else 0)
        
        print(f"📈 Overall Success Rate: {total_passed}/{total_tests} ({(total_passed/total_tests*100):.1f}%)")
        
        if bearer_failed == 0 and self.auth_token and sanity_passed:
            print("🏆 ALL LEGACY ENDPOINT TESTS PASSED!")
        else:
            print("⚠️  Some tests failed - see details above")
        
        # Print response samples
        print()
        print("📋 RESPONSE SAMPLES:")
        print("-" * 40)
        for result in self.test_results:
            if result['success'] and result['response_data']:
                print(f"{result['test']}:")
                print(f"  {json.dumps(result['response_data'], indent=2)[:200]}...")
                print()

if __name__ == "__main__":
    tester = LegacyEndpointsTester()
    tester.run_legacy_tests()