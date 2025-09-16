#!/usr/bin/env python3
"""
Rotation Lab Backend API Tests
Tests the specific endpoints requested in the review
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

class RotationLabTester:
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
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)}")
        
    def test_auth_login(self):
        """Test POST /api/auth/login with specified credentials"""
        try:
            login_data = {
                "email": "beetge@mwebbiz.co.za",
                "password": "Albee1990!"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code != 200:
                self.log_test("POST /api/auth/login", False, 
                            f"HTTP {response.status_code}: {response.text}", 
                            response.text)
                return False
            
            login_result = response.json()
            
            # Validate login response structure
            required_fields = ['access_token', 'token_type', 'user']
            missing_fields = [field for field in required_fields if field not in login_result]
            if missing_fields:
                self.log_test("POST /api/auth/login", False, 
                            f"Login response missing fields: {missing_fields}", 
                            login_result)
                return False
            
            # Store auth token for subsequent requests
            self.auth_token = login_result['access_token']
            
            self.log_test("POST /api/auth/login", True, 
                        f"Login successful, token received: {self.auth_token[:20]}...", 
                        {"user": login_result['user']})
            return True
            
        except Exception as e:
            self.log_test("POST /api/auth/login", False, f"Error: {str(e)}")
            return False

    def test_get_rotation_presets(self):
        """Test GET /api/rotation/presets"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/rotation/presets", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.get(f"{API_BASE}/rotation/presets", headers=auth_headers)
            
            if response.status_code != 200:
                self.log_test("GET /api/rotation/presets", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
            
            presets_data = response.json()
            
            # Validate response structure
            if 'items' not in presets_data:
                self.log_test("GET /api/rotation/presets", False, 
                            "Response missing 'items' array", presets_data)
                return False
            
            items = presets_data['items']
            if not isinstance(items, list):
                self.log_test("GET /api/rotation/presets", False, 
                            "'items' is not an array", presets_data)
                return False
            
            self.log_test("GET /api/rotation/presets", True, 
                        f"Retrieved {len(items)} presets", 
                        {"items_count": len(items)})
            return True
            
        except Exception as e:
            self.log_test("GET /api/rotation/presets", False, f"Error: {str(e)}")
            return False

    def test_post_rotation_preset(self):
        """Test POST /api/rotation/presets with TestPreset"""
        try:
            if not self.auth_token:
                self.log_test("POST /api/rotation/presets", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create test preset with default RotationConfig
            preset_data = {
                "name": "TestPreset",
                "config": {
                    "name": "TestPreset",
                    "capital": 100000.0,
                    "rebalance": "D",
                    "lookback_days": 126,
                    "trend_days": 200,
                    "max_positions": 1,
                    "cost_bps": 5.0,
                    "slippage_bps": 5.0,
                    "pairs": [
                        {"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}
                    ],
                    "ema_fast": 20,
                    "ema_slow": 50,
                    "rsi_len": 14,
                    "atr_len": 20,
                    "kelt_mult": 2.0,
                    "macd_fast": 12,
                    "macd_slow": 26,
                    "macd_signal": 9,
                    "consec_needed": 2,
                    "conf_threshold": 2,
                    "exec_timing": "next_open",
                    "use_inseason": False,
                    "season_months": ""
                }
            }
            
            response = self.session.post(f"{API_BASE}/rotation/presets", 
                                       json=preset_data, headers=auth_headers)
            
            if response.status_code != 200:
                self.log_test("POST /api/rotation/presets", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            if 'message' not in result:
                self.log_test("POST /api/rotation/presets", False, 
                            "Response missing 'message' field", result)
                return False
            
            self.log_test("POST /api/rotation/presets", True, 
                        f"TestPreset saved: {result['message']}", result)
            return True
            
        except Exception as e:
            self.log_test("POST /api/rotation/presets", False, f"Error: {str(e)}")
            return False

    def test_get_rotation_presets_with_testpreset(self):
        """Test GET /api/rotation/presets again to verify TestPreset exists"""
        try:
            if not self.auth_token:
                self.log_test("GET /api/rotation/presets (verify TestPreset)", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.get(f"{API_BASE}/rotation/presets", headers=auth_headers)
            
            if response.status_code != 200:
                self.log_test("GET /api/rotation/presets (verify TestPreset)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
            
            presets_data = response.json()
            items = presets_data.get('items', [])
            
            # Look for TestPreset
            test_preset = None
            for item in items:
                if item.get('name') == 'TestPreset':
                    test_preset = item
                    break
            
            if not test_preset:
                self.log_test("GET /api/rotation/presets (verify TestPreset)", False, 
                            "TestPreset not found in presets list", 
                            {"available_presets": [item.get('name') for item in items]})
                return False
            
            # Validate TestPreset structure
            if 'config' not in test_preset:
                self.log_test("GET /api/rotation/presets (verify TestPreset)", False, 
                            "TestPreset missing config", test_preset)
                return False
            
            config = test_preset['config']
            if 'pairs' not in config or not config['pairs']:
                self.log_test("GET /api/rotation/presets (verify TestPreset)", False, 
                            "TestPreset config missing pairs", config)
                return False
            
            self.log_test("GET /api/rotation/presets (verify TestPreset)", True, 
                        f"TestPreset found with {len(config['pairs'])} pairs", 
                        {"preset_name": test_preset['name'], "pairs_count": len(config['pairs'])})
            return True
            
        except Exception as e:
            self.log_test("GET /api/rotation/presets (verify TestPreset)", False, f"Error: {str(e)}")
            return False

    def test_delete_rotation_preset(self):
        """Test DELETE /api/rotation/presets/TestPreset"""
        try:
            if not self.auth_token:
                self.log_test("DELETE /api/rotation/presets/TestPreset", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            response = self.session.delete(f"{API_BASE}/rotation/presets/TestPreset", 
                                         headers=auth_headers)
            
            if response.status_code != 200:
                self.log_test("DELETE /api/rotation/presets/TestPreset", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            if 'message' not in result:
                self.log_test("DELETE /api/rotation/presets/TestPreset", False, 
                            "Response missing 'message' field", result)
                return False
            
            self.log_test("DELETE /api/rotation/presets/TestPreset", True, 
                        f"TestPreset deleted: {result['message']}", result)
            return True
            
        except Exception as e:
            self.log_test("DELETE /api/rotation/presets/TestPreset", False, f"Error: {str(e)}")
            return False

    def test_post_rotation_backtest(self):
        """Test POST /api/rotation/backtest"""
        try:
            if not self.auth_token:
                self.log_test("POST /api/rotation/backtest", False, "No auth token available")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create backtest config with specified pairs
            backtest_config = {
                "pairs": [
                    {"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}
                ],
                "capital": 100000.0,
                "lookback_days": 126,
                "rebalance": "D"
            }
            
            response = self.session.post(f"{API_BASE}/rotation/backtest", 
                                       json=backtest_config, headers=auth_headers)
            
            if response.status_code != 200:
                self.log_test("POST /api/rotation/backtest", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Validate backtest response structure
            required_fields = ['status', 'metrics', 'equity_curve']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                self.log_test("POST /api/rotation/backtest", False, 
                            f"Response missing fields: {missing_fields}", result)
                return False
            
            # Validate metrics structure
            metrics = result.get('metrics', {})
            expected_metrics = ['total_return_pct', 'max_drawdown_pct', 'sharpe_ratio']
            missing_metrics = [metric for metric in expected_metrics if metric not in metrics]
            if missing_metrics:
                self.log_test("POST /api/rotation/backtest", False, 
                            f"Metrics missing fields: {missing_metrics}", metrics)
                return False
            
            # Validate equity curve structure
            equity_curve = result.get('equity_curve', {})
            if 'dates' not in equity_curve or 'equity' not in equity_curve:
                self.log_test("POST /api/rotation/backtest", False, 
                            "Equity curve missing dates or equity arrays", equity_curve)
                return False
            
            dates = equity_curve['dates']
            equity = equity_curve['equity']
            if len(dates) != len(equity) or len(dates) == 0:
                self.log_test("POST /api/rotation/backtest", False, 
                            f"Equity curve arrays length mismatch: dates={len(dates)}, equity={len(equity)}")
                return False
            
            self.log_test("POST /api/rotation/backtest", True, 
                        f"Backtest completed: {result['status']}, {len(dates)} data points, "
                        f"Return: {metrics.get('total_return_pct', 'N/A')}%", 
                        {
                            "status": result['status'],
                            "total_return": metrics.get('total_return_pct'),
                            "max_drawdown": metrics.get('max_drawdown_pct'),
                            "data_points": len(dates)
                        })
            return True
            
        except Exception as e:
            self.log_test("POST /api/rotation/backtest", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all rotation lab tests in sequence"""
        print("🔍 Starting Rotation Lab Backend Smoke Tests")
        print("=" * 60)
        
        tests = [
            self.test_auth_login,
            self.test_get_rotation_presets,
            self.test_post_rotation_preset,
            self.test_get_rotation_presets_with_testpreset,
            self.test_delete_rotation_preset,
            self.test_post_rotation_backtest
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL {test.__name__}: Unexpected error: {str(e)}")
                failed += 1
            
            # Small delay between tests
            time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print(f"🏁 Test Results: {passed} PASSED, {failed} FAILED")
        
        if failed == 0:
            print("✅ ALL TESTS PASSED - Rotation Lab endpoints working correctly")
            return "PASS"
        else:
            print("❌ SOME TESTS FAILED - Issues found with Rotation Lab endpoints")
            return "FAIL"

def main():
    tester = RotationLabTester()
    result = tester.run_all_tests()
    
    print(f"\n🎯 FINAL RESULT: {result}")
    
    # Print sample responses for successful tests
    print("\n📋 Sample Response Data:")
    for test_result in tester.test_results:
        if test_result['success'] and test_result['response_data']:
            print(f"\n{test_result['test']}:")
            print(json.dumps(test_result['response_data'], indent=2))

if __name__ == "__main__":
    main()