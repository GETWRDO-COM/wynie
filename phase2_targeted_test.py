#!/usr/bin/env python3
"""
Phase 2 Targeted Backend API Tests
Re-run targeted backend tests after fixes for the specific endpoints mentioned in review request
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

class Phase2TargetedTester:
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
        """Authenticate and get token"""
        try:
            login_data = {
                "email": "beetge@mwebbiz.co.za",
                "password": "Albee1990!"
            }
            
            login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            if login_response.status_code != 200:
                self.log_test("Authentication", False, f"Login failed: HTTP {login_response.status_code}: {login_response.text}")
                return False
            
            login_result = login_response.json()
            self.auth_token = login_result.get('access_token')
            
            if not self.auth_token:
                self.log_test("Authentication", False, "No access token received")
                return False
                
            self.log_test("Authentication", True, "Successfully authenticated")
            return True
            
        except Exception as e:
            self.log_test("Authentication", False, f"Error: {str(e)}")
            return False

    def test_universe_import(self):
        """Test Phase 2: POST /api/universe/import with AAPL, MSFT, NVDA → 200 with {imported:3}; GET /api/universe contains those symbols"""
        try:
            if not self.auth_token:
                self.log_test("Universe Import", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test import with the specific symbols mentioned in review request
            import_data = [
                {"symbol": "AAPL"},
                {"symbol": "MSFT"},
                {"symbol": "NVDA"}
            ]
            
            print(f"Testing POST {API_BASE}/universe/import with {import_data}")
            response = self.session.post(f"{API_BASE}/universe/import", json=import_data, headers=auth_headers)
            
            if response.status_code != 200:
                self.log_test("Universe Import", False, f"POST /api/universe/import failed: HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            print(f"Import response: {result}")
            
            # Validate response structure - should have {imported: 3}
            if 'imported' not in result:
                self.log_test("Universe Import", False, "Response missing 'imported' field")
                return False
            
            imported_count = result.get('imported', 0)
            if imported_count != 3:
                self.log_test("Universe Import", False, f"Expected imported:3, got imported:{imported_count}")
                return False
            
            # Verify by getting universe - should contain those symbols
            print(f"Testing GET {API_BASE}/universe")
            get_response = self.session.get(f"{API_BASE}/universe")
            if get_response.status_code != 200:
                self.log_test("Universe Import", False, f"GET /api/universe failed: HTTP {get_response.status_code}: {get_response.text}")
                return False
            
            universe = get_response.json()
            print(f"Universe response type: {type(universe)}, length: {len(universe) if isinstance(universe, list) else 'N/A'}")
            
            if not isinstance(universe, list):
                self.log_test("Universe Import", False, f"GET /api/universe should return array, got {type(universe)}")
                return False
            
            # Check if our imported symbols are present
            universe_symbols = {item.get('symbol', '').upper() for item in universe}
            expected_symbols = {'AAPL', 'MSFT', 'NVDA'}
            
            print(f"Universe symbols: {sorted(universe_symbols)}")
            print(f"Expected symbols: {sorted(expected_symbols)}")
            
            if not expected_symbols.issubset(universe_symbols):
                missing = expected_symbols - universe_symbols
                self.log_test("Universe Import", False, f"Missing imported symbols in universe: {missing}")
                return False
            
            self.log_test("Universe Import", True, f"✅ POST /api/universe/import → 200 with imported:3; GET /api/universe contains AAPL, MSFT, NVDA")
            return True
            
        except Exception as e:
            self.log_test("Universe Import", False, f"Error: {str(e)}")
            return False

    def test_screens_neglected_pre_earnings(self):
        """Test Phase 2: GET /api/screens/neglected-pre-earnings returns 200 and array items with label WATCH/READY"""
        try:
            print(f"Testing GET {API_BASE}/screens/neglected-pre-earnings")
            response = self.session.get(f"{API_BASE}/screens/neglected-pre-earnings")
            
            if response.status_code != 200:
                self.log_test("Screens Neglected Pre-Earnings", False, f"GET /api/screens/neglected-pre-earnings failed: HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            print(f"Screen response type: {type(result)}, length: {len(result) if isinstance(result, list) else 'N/A'}")
            
            # Should be an array (can be empty)
            if not isinstance(result, list):
                self.log_test("Screens Neglected Pre-Earnings", False, f"Expected array, got {type(result)}")
                return False
            
            # If not empty, validate structure and WATCH/READY labels
            if len(result) > 0:
                print(f"Sample screen item: {result[0]}")
                sample_item = result[0]
                
                # Check for required fields
                required_fields = ['symbol', 'label']
                missing_fields = [field for field in required_fields if field not in sample_item]
                if missing_fields:
                    self.log_test("Screens Neglected Pre-Earnings", False, f"Screen item missing fields: {missing_fields}")
                    return False
                
                # Validate label is WATCH or READY
                label = sample_item.get('label')
                if label not in ['WATCH', 'READY']:
                    self.log_test("Screens Neglected Pre-Earnings", False, f"Invalid label: {label}, expected WATCH or READY")
                    return False
                
                # Check all items have valid labels
                invalid_labels = []
                for item in result:
                    item_label = item.get('label')
                    if item_label not in ['WATCH', 'READY']:
                        invalid_labels.append(f"{item.get('symbol', 'UNKNOWN')}:{item_label}")
                
                if invalid_labels:
                    self.log_test("Screens Neglected Pre-Earnings", False, f"Items with invalid labels: {invalid_labels}")
                    return False
            
            self.log_test("Screens Neglected Pre-Earnings", True, f"✅ GET /api/screens/neglected-pre-earnings → 200 with {len(result)} items, all have valid WATCH/READY labels")
            return True
            
        except Exception as e:
            self.log_test("Screens Neglected Pre-Earnings", False, f"Error: {str(e)}")
            return False

    def test_etf_regime_simulate(self):
        """Test Phase 2: POST /api/signals/etf-regime/simulate with body {"start":"2024-01-01","end":"2024-01-31"} returns all required fields"""
        try:
            # Test with a longer date range to meet the 60-day requirement
            simulate_data = {
                "start": "2024-01-01",
                "end": "2024-03-31"  # Extended to ~90 days
            }
            
            print(f"Testing POST {API_BASE}/signals/etf-regime/simulate with {simulate_data}")
            response = self.session.post(f"{API_BASE}/signals/etf-regime/simulate", json=simulate_data)
            
            if response.status_code != 200:
                self.log_test("ETF Regime Simulate", False, f"POST /api/signals/etf-regime/simulate failed: HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            print(f"Simulate response keys: {list(result.keys())}")
            
            # Validate all required fields from review request
            required_fields = [
                'equity_curve', 'total_return', 'max_drawdown', 'sharpe', 
                'flips', 'pl_by_regime', 'decisions', 'params_version'
            ]
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                self.log_test("ETF Regime Simulate", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Validate equity_curve structure
            equity_curve = result.get('equity_curve', [])
            if not isinstance(equity_curve, list):
                self.log_test("ETF Regime Simulate", False, f"equity_curve should be array, got {type(equity_curve)}")
                return False
            
            # Validate decisions structure
            decisions = result.get('decisions', [])
            if not isinstance(decisions, list):
                self.log_test("ETF Regime Simulate", False, f"decisions should be array, got {type(decisions)}")
                return False
            
            # Validate pl_by_regime structure
            pl_by_regime = result.get('pl_by_regime', {})
            if not isinstance(pl_by_regime, dict):
                self.log_test("ETF Regime Simulate", False, f"pl_by_regime should be dict, got {type(pl_by_regime)}")
                return False
            
            # Validate numeric fields
            numeric_fields = ['total_return', 'max_drawdown', 'sharpe', 'flips']
            for field in numeric_fields:
                value = result.get(field)
                if not isinstance(value, (int, float)):
                    self.log_test("ETF Regime Simulate", False, f"{field} should be numeric, got {type(value)}")
                    return False
            
            # Validate params_version is string
            params_version = result.get('params_version')
            if not isinstance(params_version, str):
                self.log_test("ETF Regime Simulate", False, f"params_version should be string, got {type(params_version)}")
                return False
            
            print(f"Simulation results: equity_curve={len(equity_curve)} points, decisions={len(decisions)}, flips={result['flips']}, total_return={result['total_return']:.2%}")
            
            self.log_test("ETF Regime Simulate", True, f"✅ POST /api/signals/etf-regime/simulate → 200 with all required fields: equity_curve, total_return, max_drawdown, sharpe, flips, pl_by_regime, decisions, params_version")
            return True
            
        except Exception as e:
            self.log_test("ETF Regime Simulate", False, f"Error: {str(e)}")
            return False

    def run_targeted_tests(self):
        """Run the three specific Phase 2 tests mentioned in review request"""
        print("🎯 PHASE 2 TARGETED BACKEND TESTING")
        print("=" * 60)
        print("Testing the three specific endpoints mentioned in review request:")
        print("1. Auth then POST /api/universe/import → 200 with {imported:3}")
        print("2. GET /api/screens/neglected-pre-earnings → 200 with WATCH/READY labels")
        print("3. POST /api/signals/etf-regime/simulate → 200 with all required fields")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with tests")
            return
        
        # Run the three targeted tests
        test_methods = [
            self.test_universe_import,
            self.test_screens_neglected_pre_earnings,
            self.test_etf_regime_simulate
        ]
        
        passed = 0
        total = len(test_methods)
        
        for test_method in test_methods:
            try:
                if test_method():
                    passed += 1
                print()  # Add spacing between tests
            except Exception as e:
                print(f"❌ Test {test_method.__name__} crashed: {e}")
        
        print("=" * 60)
        print(f"🎯 PHASE 2 TARGETED TEST RESULTS: {passed}/{total} PASSED")
        
        if passed == total:
            print("✅ ALL PHASE 2 TARGETED TESTS PASSED!")
        else:
            print(f"❌ {total - passed} TESTS FAILED")
            
        print("=" * 60)
        
        return passed, total, self.test_results

if __name__ == "__main__":
    tester = Phase2TargetedTester()
    passed, total, results = tester.run_targeted_tests()
    
    # Print detailed results
    print("\n📋 DETAILED TEST RESULTS:")
    for result in results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}: {result['details']}")