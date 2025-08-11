#!/usr/bin/env python3
"""
Backend API Testing Suite
Tests all FastAPI endpoints for the Deepvue-like workstation
"""

import requests
import json
import sys
from datetime import datetime
import time
import websocket
import threading
import asyncio

# Get backend URL from frontend .env
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not get REACT_APP_BACKEND_URL from frontend/.env")
    sys.exit(1)

print(f"Testing backend at: {BASE_URL}")

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = {
            'marketdata': {'passed': 0, 'failed': 0, 'errors': []},
            'watchlists': {'passed': 0, 'failed': 0, 'errors': []},
            'columns': {'passed': 0, 'failed': 0, 'errors': []},
            'ratings': {'passed': 0, 'failed': 0, 'errors': []}
        }
        
    def log_result(self, category, test_name, success, error_msg=None):
        if success:
            self.test_results[category]['passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['errors'].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")
    
    def test_marketdata_endpoints(self):
        print("\n=== Testing Market Data Endpoints ===")
        
        # Test 1: Symbol Search
        try:
            response = self.session.get(f"{self.base_url}/api/marketdata/symbols/search?q=AAPL")
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and isinstance(data['items'], list):
                    self.log_result('marketdata', 'Symbol Search - AAPL', True)
                else:
                    self.log_result('marketdata', 'Symbol Search - AAPL', False, f"Invalid response structure: {data}")
            else:
                self.log_result('marketdata', 'Symbol Search - AAPL', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('marketdata', 'Symbol Search - AAPL', False, str(e))
        
        # Test 2: Bars Data
        try:
            response = self.session.get(f"{self.base_url}/api/marketdata/bars?symbol=AAPL&interval=1D")
            if response.status_code == 200:
                data = response.json()
                if 'symbol' in data and 'bars' in data and isinstance(data['bars'], list):
                    self.log_result('marketdata', 'Bars Data - AAPL 1D', True)
                else:
                    self.log_result('marketdata', 'Bars Data - AAPL 1D', False, f"Invalid response structure: {data}")
            else:
                self.log_result('marketdata', 'Bars Data - AAPL 1D', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('marketdata', 'Bars Data - AAPL 1D', False, str(e))
        
        # Test 3: Quotes
        try:
            response = self.session.get(f"{self.base_url}/api/marketdata/quotes?symbols=AAPL,MSFT")
            if response.status_code == 200:
                data = response.json()
                if 'quotes' in data and isinstance(data['quotes'], list):
                    self.log_result('marketdata', 'Quotes - AAPL,MSFT', True)
                else:
                    self.log_result('marketdata', 'Quotes - AAPL,MSFT', False, f"Invalid response structure: {data}")
            else:
                self.log_result('marketdata', 'Quotes - AAPL,MSFT', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('marketdata', 'Quotes - AAPL,MSFT', False, str(e))
        
        # Test 4: Logo
        try:
            response = self.session.get(f"{self.base_url}/api/marketdata/logo?symbol=AAPL")
            if response.status_code == 200:
                data = response.json()
                if 'symbol' in data and 'logoUrl' in data:
                    self.log_result('marketdata', 'Logo - AAPL', True)
                else:
                    self.log_result('marketdata', 'Logo - AAPL', False, f"Invalid response structure: {data}")
            else:
                self.log_result('marketdata', 'Logo - AAPL', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('marketdata', 'Logo - AAPL', False, str(e))
        
        # Test 5: Error handling - missing parameter
        try:
            response = self.session.get(f"{self.base_url}/api/marketdata/symbols/search")
            if response.status_code == 422:  # FastAPI validation error
                self.log_result('marketdata', 'Error Handling - Missing q param', True)
            else:
                self.log_result('marketdata', 'Error Handling - Missing q param', False, f"Expected 422, got {response.status_code}")
        except Exception as e:
            self.log_result('marketdata', 'Error Handling - Missing q param', False, str(e))
    
    def test_watchlists_crud(self):
        print("\n=== Testing Watchlists CRUD ===")
        test_watchlist_id = None
        
        # Test 1: Create Watchlist
        try:
            payload = {"name": "Test Portfolio", "symbols": ["AAPL", "MSFT", "GOOGL"]}
            response = self.session.post(f"{self.base_url}/api/watchlists", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and 'name' in data and 'symbols' in data:
                    test_watchlist_id = data['id']
                    self.log_result('watchlists', 'Create Watchlist', True)
                else:
                    self.log_result('watchlists', 'Create Watchlist', False, f"Invalid response structure: {data}")
            else:
                self.log_result('watchlists', 'Create Watchlist', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('watchlists', 'Create Watchlist', False, str(e))
        
        # Test 2: List Watchlists
        try:
            response = self.session.get(f"{self.base_url}/api/watchlists")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result('watchlists', 'List Watchlists', True)
                else:
                    self.log_result('watchlists', 'List Watchlists', False, f"Expected list, got: {type(data)}")
            else:
                self.log_result('watchlists', 'List Watchlists', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('watchlists', 'List Watchlists', False, str(e))
        
        # Test 3: Update Watchlist (if we have an ID)
        if test_watchlist_id:
            try:
                payload = {"name": "Updated Test Portfolio", "symbols": ["AAPL", "TSLA"]}
                response = self.session.put(f"{self.base_url}/api/watchlists/{test_watchlist_id}", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    if 'name' in data:
                        self.log_result('watchlists', 'Update Watchlist', True)
                    else:
                        self.log_result('watchlists', 'Update Watchlist', False, f"Invalid response structure: {data}")
                else:
                    self.log_result('watchlists', 'Update Watchlist', False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result('watchlists', 'Update Watchlist', False, str(e))
        
        # Test 4: Delete Watchlist (if we have an ID)
        if test_watchlist_id:
            try:
                response = self.session.delete(f"{self.base_url}/api/watchlists/{test_watchlist_id}")
                if response.status_code == 200:
                    data = response.json()
                    if 'ok' in data and data['ok']:
                        self.log_result('watchlists', 'Delete Watchlist', True)
                    else:
                        self.log_result('watchlists', 'Delete Watchlist', False, f"Invalid response: {data}")
                else:
                    self.log_result('watchlists', 'Delete Watchlist', False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_result('watchlists', 'Delete Watchlist', False, str(e))
        
        # Test 5: Error handling - Update non-existent watchlist
        try:
            payload = {"name": "Non-existent"}
            response = self.session.put(f"{self.base_url}/api/watchlists/non-existent-id", json=payload)
            if response.status_code == 404:
                self.log_result('watchlists', 'Error Handling - Update non-existent', True)
            else:
                self.log_result('watchlists', 'Error Handling - Update non-existent', False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_result('watchlists', 'Error Handling - Update non-existent', False, str(e))
    
    def test_columns_endpoints(self):
        print("\n=== Testing Columns Endpoints ===")
        
        # Test 1: Get Columns Schema
        try:
            response = self.session.get(f"{self.base_url}/api/columns/schema")
            if response.status_code == 200:
                data = response.json()
                if 'categories' in data and isinstance(data['categories'], list):
                    self.log_result('columns', 'Get Columns Schema', True)
                else:
                    self.log_result('columns', 'Get Columns Schema', False, f"Invalid response structure: {data}")
            else:
                self.log_result('columns', 'Get Columns Schema', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('columns', 'Get Columns Schema', False, str(e))
        
        # Test 2: Get Column Presets
        try:
            response = self.session.get(f"{self.base_url}/api/columns/presets")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    self.log_result('columns', 'Get Column Presets', True)
                else:
                    self.log_result('columns', 'Get Column Presets', False, f"Expected dict, got: {type(data)}")
            else:
                self.log_result('columns', 'Get Column Presets', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('columns', 'Get Column Presets', False, str(e))
        
        # Test 3: Save Column Preset
        try:
            payload = {"name": "Test Preset", "columns": ["symbol", "last", "changePct", "volume"]}
            response = self.session.post(f"{self.base_url}/api/columns/presets", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'ok' in data and data['ok']:
                    self.log_result('columns', 'Save Column Preset', True)
                else:
                    self.log_result('columns', 'Save Column Preset', False, f"Invalid response: {data}")
            else:
                self.log_result('columns', 'Save Column Preset', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('columns', 'Save Column Preset', False, str(e))
        
        # Test 4: Delete Column Preset
        try:
            response = self.session.delete(f"{self.base_url}/api/columns/presets/Test Preset")
            if response.status_code == 200:
                data = response.json()
                if 'ok' in data and data['ok']:
                    self.log_result('columns', 'Delete Column Preset', True)
                else:
                    self.log_result('columns', 'Delete Column Preset', False, f"Invalid response: {data}")
            else:
                self.log_result('columns', 'Delete Column Preset', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('columns', 'Delete Column Preset', False, str(e))
    
    def test_ratings_compute(self):
        print("\n=== Testing Ratings Compute ===")
        
        # Test 1: Compute RS/AS ratings
        try:
            payload = {
                "symbols": ["AAPL", "MSFT"],
                "rsWindowDays": 63,
                "asShortDays": 21,
                "asLongDays": 63
            }
            response = self.session.post(f"{self.base_url}/api/ratings/compute", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'RS' in data and 'AS' in data and isinstance(data['RS'], dict) and isinstance(data['AS'], dict):
                    # Check if we have ratings for the requested symbols
                    if 'AAPL' in data['RS'] and 'MSFT' in data['RS']:
                        self.log_result('ratings', 'Compute RS/AS - AAPL,MSFT', True)
                    else:
                        self.log_result('ratings', 'Compute RS/AS - AAPL,MSFT', False, f"Missing symbol ratings: {data}")
                else:
                    self.log_result('ratings', 'Compute RS/AS - AAPL,MSFT', False, f"Invalid response structure: {data}")
            else:
                self.log_result('ratings', 'Compute RS/AS - AAPL,MSFT', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('ratings', 'Compute RS/AS - AAPL,MSFT', False, str(e))
        
        # Test 2: Error handling - missing symbols
        try:
            payload = {"rsWindowDays": 63}  # Missing symbols
            response = self.session.post(f"{self.base_url}/api/ratings/compute", json=payload)
            if response.status_code == 422:  # FastAPI validation error
                self.log_result('ratings', 'Error Handling - Missing symbols', True)
            else:
                self.log_result('ratings', 'Error Handling - Missing symbols', False, f"Expected 422, got {response.status_code}")
        except Exception as e:
            self.log_result('ratings', 'Error Handling - Missing symbols', False, str(e))
        
        # Test 3: Custom window parameters
        try:
            payload = {
                "symbols": ["AAPL"],
                "rsWindowDays": 30,
                "asShortDays": 10,
                "asLongDays": 30
            }
            response = self.session.post(f"{self.base_url}/api/ratings/compute", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'RS' in data and 'AS' in data and 'AAPL' in data['RS']:
                    self.log_result('ratings', 'Custom Window Parameters', True)
                else:
                    self.log_result('ratings', 'Custom Window Parameters', False, f"Invalid response: {data}")
            else:
                self.log_result('ratings', 'Custom Window Parameters', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('ratings', 'Custom Window Parameters', False, str(e))
    
    def run_all_tests(self):
        print(f"Starting Backend API Tests at {datetime.now()}")
        print(f"Base URL: {self.base_url}")
        
        self.test_marketdata_endpoints()
        self.test_watchlists_crud()
        self.test_columns_endpoints()
        self.test_ratings_compute()
        
        self.print_summary()
    
    def print_summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        total_passed = 0
        total_failed = 0
        
        for category, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total_passed += passed
            total_failed += failed
            
            status = "✅ PASS" if failed == 0 else "❌ FAIL"
            print(f"{category.upper()}: {status} ({passed} passed, {failed} failed)")
            
            if results['errors']:
                for error in results['errors']:
                    print(f"  - {error}")
        
        print("-" * 60)
        overall_status = "✅ ALL TESTS PASSED" if total_failed == 0 else f"❌ {total_failed} TESTS FAILED"
        print(f"OVERALL: {overall_status} ({total_passed} passed, {total_failed} failed)")
        print("="*60)

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()