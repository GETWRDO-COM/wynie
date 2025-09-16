#!/usr/bin/env python3
"""
HUNT by WRDO Dashboard API Testing - Review Request Focus
Tests the newly implemented dashboard API endpoints as specified in the review request
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

# Test credentials from review request
TEST_EMAIL = "beetge@mwebbiz.co.za"
TEST_PASSWORD = "Albee1990!"

class ReviewRequestTester:
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
        
    def authenticate(self):
        """Authenticate and get Bearer token"""
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            if response.status_code != 200:
                self.log_test("Authentication", False, f"Login failed: HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            if 'access_token' not in result:
                self.log_test("Authentication", False, "Login response missing access_token")
                return False
            
            self.auth_token = result['access_token']
            self.log_test("Authentication", True, f"Successfully authenticated as {TEST_EMAIL}")
            return True
            
        except Exception as e:
            self.log_test("Authentication", False, f"Authentication error: {str(e)}")
            return False

    def test_fixed_critical_apis(self):
        """Test FIXED CRITICAL APIs that were showing N/A before"""
        
        # 1. GET /api/greed-fear - Should return actual Fear & Greed score
        try:
            response = self.session.get(f"{API_BASE}/greed-fear")
            if response.status_code != 200:
                self.log_test("Fear & Greed API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['now', 'last_updated']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Fear & Greed API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate score is numeric and in valid range (0-100)
            score = data.get('now')
            if not isinstance(score, (int, float)) or not (0 <= score <= 100):
                self.log_test("Fear & Greed API", False, f"Invalid score: {score} (should be 0-100)")
                return False
            
            # Check for historical data
            historical_fields = ['previous_close', 'one_week_ago', 'one_month_ago']
            has_historical = any(field in data for field in historical_fields)
            
            self.log_test("Fear & Greed API", True, f"Score: {score}, Historical data: {has_historical}")
            
        except Exception as e:
            self.log_test("Fear & Greed API", False, f"Error: {str(e)}")
            return False

        # 2. GET /api/market-score - Should return calculated market score
        try:
            response = self.session.get(f"{API_BASE}/market-score")
            if response.status_code != 200:
                self.log_test("Market Score API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['score', 'trend', 'recommendation', 'last_updated']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Market Score API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate score is numeric
            score = data.get('score')
            if not isinstance(score, (int, float)):
                self.log_test("Market Score API", False, f"Invalid score type: {type(score)}")
                return False
            
            # Validate trend and recommendation are not N/A or empty
            trend = data.get('trend', '')
            recommendation = data.get('recommendation', '')
            
            if trend in ['N/A', '', 'Not found'] or recommendation in ['N/A', '', 'Not found']:
                self.log_test("Market Score API", False, f"Trend or recommendation still showing N/A: {trend}, {recommendation}")
                return False
            
            self.log_test("Market Score API", True, f"Score: {score}, Trend: {trend}")
            
        except Exception as e:
            self.log_test("Market Score API", False, f"Error: {str(e)}")
            return False

        # 3. GET /api/dashboard - Should return SA greetings and timezone data
        if not self.auth_token:
            self.log_test("Dashboard API", False, "No auth token - authentication required")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{API_BASE}/dashboard", headers=headers)
            if response.status_code != 200:
                self.log_test("Dashboard API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['user_greeting', 'timezone_data']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Dashboard API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate SA greeting
            greeting = data.get('user_greeting', '')
            sa_greetings = ['Goeie Môre', 'Goeie Middag', 'Goeie Aand', 'Goeie Nag']
            has_sa_greeting = any(sa_greeting in greeting for sa_greeting in sa_greetings)
            
            if not has_sa_greeting:
                self.log_test("Dashboard API", False, f"No SA greeting found in: {greeting}")
                return False
            
            # Validate timezone data
            timezone_data = data.get('timezone_data', {})
            required_timezones = ['south_africa', 'new_york']
            missing_timezones = [tz for tz in required_timezones if tz not in timezone_data]
            if missing_timezones:
                self.log_test("Dashboard API", False, f"Missing timezone data: {missing_timezones}")
                return False
            
            self.log_test("Dashboard API", True, f"SA greeting: {greeting[:50]}..., Timezones: {list(timezone_data.keys())}")
            
        except Exception as e:
            self.log_test("Dashboard API", False, f"Error: {str(e)}")
            return False

        return True

    def test_new_missing_endpoints(self):
        """Test NEW MISSING ENDPOINTS that are completely new"""
        
        if not self.auth_token:
            self.log_test("New Endpoints", False, "No auth token - authentication required")
            return False
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # 1. GET /api/news?category=All - Enhanced news with multiple categories
        try:
            response = self.session.get(f"{API_BASE}/news?category=All")
            if response.status_code != 200:
                self.log_test("Enhanced News API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['articles', 'category', 'total_count']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Enhanced News API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate articles array
            articles = data.get('articles', [])
            if not isinstance(articles, list) or len(articles) == 0:
                self.log_test("Enhanced News API", False, f"No articles returned: {len(articles)}")
                return False
            
            # Validate article structure
            sample_article = articles[0]
            required_article_fields = ['title', 'source', 'published', 'url']
            missing_article_fields = [field for field in required_article_fields if field not in sample_article]
            if missing_article_fields:
                self.log_test("Enhanced News API", False, f"Article missing fields: {missing_article_fields}")
                return False
            
            self.log_test("Enhanced News API", True, f"Category: {data['category']}, Articles: {len(articles)}")
            
        except Exception as e:
            self.log_test("Enhanced News API", False, f"Error: {str(e)}")
            return False

        # 2. GET /api/earnings - Earnings calendar data
        try:
            response = self.session.get(f"{API_BASE}/earnings")
            if response.status_code != 200:
                self.log_test("Earnings Calendar API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['earnings', 'total_count']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Earnings Calendar API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate earnings array
            earnings = data.get('earnings', [])
            if not isinstance(earnings, list):
                self.log_test("Earnings Calendar API", False, f"Earnings not an array: {type(earnings)}")
                return False
            
            if len(earnings) > 0:
                # Validate earnings structure
                sample_earning = earnings[0]
                required_earning_fields = ['ticker', 'company_name', 'date', 'quarter']
                missing_earning_fields = [field for field in required_earning_fields if field not in sample_earning]
                if missing_earning_fields:
                    self.log_test("Earnings Calendar API", False, f"Earning missing fields: {missing_earning_fields}")
                    return False
            
            self.log_test("Earnings Calendar API", True, f"Earnings count: {len(earnings)}")
            
        except Exception as e:
            self.log_test("Earnings Calendar API", False, f"Error: {str(e)}")
            return False

        # 3. GET /api/watchlists/custom - User watchlists
        try:
            response = self.session.get(f"{API_BASE}/watchlists/custom", headers=headers)
            if response.status_code != 200:
                self.log_test("Custom Watchlists API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['watchlists', 'total_count']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Custom Watchlists API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate watchlists array
            watchlists = data.get('watchlists', [])
            if not isinstance(watchlists, list):
                self.log_test("Custom Watchlists API", False, f"Watchlists not an array: {type(watchlists)}")
                return False
            
            if len(watchlists) > 0:
                # Validate watchlist structure
                sample_watchlist = watchlists[0]
                required_watchlist_fields = ['id', 'name', 'tickers']
                missing_watchlist_fields = [field for field in required_watchlist_fields if field not in sample_watchlist]
                if missing_watchlist_fields:
                    self.log_test("Custom Watchlists API", False, f"Watchlist missing fields: {missing_watchlist_fields}")
                    return False
            
            self.log_test("Custom Watchlists API", True, f"Watchlists count: {len(watchlists)}")
            
        except Exception as e:
            self.log_test("Custom Watchlists API", False, f"Error: {str(e)}")
            return False

        # 4. GET /api/portfolio/performance - Portfolio performance data
        try:
            response = self.session.get(f"{API_BASE}/portfolio/performance", headers=headers)
            if response.status_code != 200:
                self.log_test("Portfolio Performance API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate response structure
            required_fields = ['data', 'last_updated']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Portfolio Performance API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate data structure
            portfolio_data = data.get('data', {})
            if not isinstance(portfolio_data, dict):
                self.log_test("Portfolio Performance API", False, f"Data not a dict: {type(portfolio_data)}")
                return False
            
            # Check for expected portfolios
            expected_portfolios = ['Total']
            found_portfolios = [p for p in expected_portfolios if p in portfolio_data]
            
            if len(found_portfolios) == 0:
                self.log_test("Portfolio Performance API", False, f"No expected portfolios found: {list(portfolio_data.keys())}")
                return False
            
            # Validate portfolio structure
            sample_portfolio = portfolio_data[found_portfolios[0]]
            if not isinstance(sample_portfolio, dict):
                self.log_test("Portfolio Performance API", False, f"Portfolio data not a dict: {type(sample_portfolio)}")
                return False
            
            self.log_test("Portfolio Performance API", True, f"Portfolios: {list(portfolio_data.keys())}")
            
        except Exception as e:
            self.log_test("Portfolio Performance API", False, f"Error: {str(e)}")
            return False

        return True

    def test_authentication_flow(self):
        """Test authentication endpoints specifically"""
        
        # Test login endpoint
        try:
            login_data = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            if response.status_code != 200:
                self.log_test("Auth Login", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            required_fields = ['access_token', 'token_type', 'user']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                self.log_test("Auth Login", False, f"Missing fields: {missing_fields}")
                return False
            
            # Test /auth/me endpoint
            token = result['access_token']
            headers = {"Authorization": f"Bearer {token}"}
            
            me_response = self.session.get(f"{API_BASE}/auth/me", headers=headers)
            if me_response.status_code != 200:
                self.log_test("Auth Me", False, f"HTTP {me_response.status_code}: {me_response.text}")
                return False
            
            user_info = me_response.json()
            if user_info.get('email') != TEST_EMAIL:
                self.log_test("Auth Me", False, f"Email mismatch: {user_info.get('email')} != {TEST_EMAIL}")
                return False
            
            self.log_test("Authentication Flow", True, f"Login and user info retrieval successful for {TEST_EMAIL}")
            return True
            
        except Exception as e:
            self.log_test("Authentication Flow", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run all tests in the review request"""
        print("🎯 HUNT by WRDO Dashboard API Testing - Review Request Focus")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Credentials: {TEST_EMAIL}")
        print("=" * 80)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with protected endpoints")
            return False
        
        # Step 2: Test Fixed Critical APIs
        print("\n🔧 Testing FIXED CRITICAL APIs (previously showing N/A):")
        fixed_apis_success = self.test_fixed_critical_apis()
        
        # Step 3: Test New Missing Endpoints
        print("\n🆕 Testing NEW MISSING ENDPOINTS:")
        new_endpoints_success = self.test_new_missing_endpoints()
        
        # Step 4: Test Authentication Flow
        print("\n🔐 Testing AUTHENTICATION FLOW:")
        auth_success = self.test_authentication_flow()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY:")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}: {result['details']}")
        
        overall_success = fixed_apis_success and new_endpoints_success and auth_success
        
        if overall_success:
            print("\n🏆 ALL CRITICAL ENDPOINTS WORKING - DASHBOARD READY FOR PRODUCTION!")
        else:
            print("\n⚠️  SOME ENDPOINTS NEED ATTENTION - SEE FAILED TESTS ABOVE")
        
        return overall_success

if __name__ == "__main__":
    tester = ReviewRequestTester()
    success = tester.run_comprehensive_test()
    exit(0 if success else 1)