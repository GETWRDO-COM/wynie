#!/usr/bin/env python3
"""
Comprehensive Rotation Lab Backend Test
Tests all rotation endpoints as requested in the review request
"""

import requests
import json
import sys
from datetime import datetime

# Configuration from review request
BACKEND_URL = "https://trade-dashboard-37.preview.emergentagent.com"
LOGIN_EMAIL = "beetge@mwebbiz.co.za"
LOGIN_PASSWORD = "Albee1990!"

# Sample data from review request
SAMPLE_ROTATION_CONFIG = {
    "name": "Test Config",
    "capital": 100000.0,
    "rebalance": "D",
    "pairs": [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}],
    "ema_fast": 20,
    "ema_slow": 50,
    "conf_threshold": 2
}

SAMPLE_PRESET = {
    "name": "TestPreset",
    "config": SAMPLE_ROTATION_CONFIG
}

SAMPLE_BACKTEST_CONFIG = {
    "pairs": [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}],
    "capital": 100000.0
}

class ComprehensiveRotationTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        
    def authenticate(self):
        """Step 1: Authentication Setup"""
        print("🔐 STEP 1: Authentication Setup")
        try:
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if self.token:
                    self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                    self.log_result("Authentication", True, "Login successful, JWT token received")
                    return True
                else:
                    self.log_result("Authentication", False, "No access token in response")
                    return False
            else:
                self.log_result("Authentication", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_rotation_config_get(self):
        """Test GET /api/rotation/config"""
        try:
            response = self.session.get(f"{BACKEND_URL}/api/rotation/config")
            if response.status_code == 200:
                data = response.json()
                if "owner" in data and "config" in data:
                    config = data["config"]
                    self.log_result("GET /api/rotation/config", True, 
                                  f"Retrieved config for {data['owner']}, pairs: {len(config.get('pairs', []))}")
                    return True
                else:
                    self.log_result("GET /api/rotation/config", False, f"Invalid response structure: {data}")
                    return False
            else:
                self.log_result("GET /api/rotation/config", False, f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("GET /api/rotation/config", False, f"Exception: {str(e)}")
            return False
    
    def test_rotation_config_post(self):
        """Test POST /api/rotation/config"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/api/rotation/config",
                json=SAMPLE_ROTATION_CONFIG,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "saved":
                    self.log_result("POST /api/rotation/config", True, "Config saved successfully")
                    return True
                else:
                    self.log_result("POST /api/rotation/config", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("POST /api/rotation/config", False, f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("POST /api/rotation/config", False, f"Exception: {str(e)}")
            return False
    
    def test_rotation_presets_get(self):
        """Test GET /api/rotation/presets"""
        try:
            response = self.session.get(f"{BACKEND_URL}/api/rotation/presets")
            if response.status_code == 200:
                data = response.json()
                if "items" in data and isinstance(data["items"], list):
                    self.log_result("GET /api/rotation/presets", True, f"Retrieved {len(data['items'])} presets")
                    return True
                else:
                    self.log_result("GET /api/rotation/presets", False, f"Invalid response structure: {data}")
                    return False
            else:
                self.log_result("GET /api/rotation/presets", False, f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("GET /api/rotation/presets", False, f"Exception: {str(e)}")
            return False
    
    def test_rotation_presets_post(self):
        """Test POST /api/rotation/presets"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/api/rotation/presets",
                json=SAMPLE_PRESET,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "saved":
                    self.log_result("POST /api/rotation/presets", True, f"Preset '{SAMPLE_PRESET['name']}' saved")
                    return True
                else:
                    self.log_result("POST /api/rotation/presets", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("POST /api/rotation/presets", False, f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("POST /api/rotation/presets", False, f"Exception: {str(e)}")
            return False
    
    def test_rotation_presets_delete(self):
        """Test DELETE /api/rotation/presets/{name}"""
        try:
            response = self.session.delete(f"{BACKEND_URL}/api/rotation/presets/{SAMPLE_PRESET['name']}")
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "deleted":
                    self.log_result("DELETE /api/rotation/presets", True, f"Preset '{SAMPLE_PRESET['name']}' deleted")
                    return True
                else:
                    self.log_result("DELETE /api/rotation/presets", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_result("DELETE /api/rotation/presets", False, f"Status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_result("DELETE /api/rotation/presets", False, f"Exception: {str(e)}")
            return False
    
    def test_rotation_backtest(self):
        """Test POST /api/rotation/backtest"""
        try:
            response = self.session.post(
                f"{BACKEND_URL}/api/rotation/backtest",
                json=SAMPLE_BACKTEST_CONFIG,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ["config", "metrics", "equity_curve"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result("POST /api/rotation/backtest", False, f"Missing fields: {missing_fields}")
                    return False
                
                # Check metrics
                metrics = data.get("metrics", {})
                required_metrics = ["cagr", "max_dd", "sharpe", "total_return"]
                missing_metrics = [metric for metric in required_metrics if metric not in metrics]
                
                if missing_metrics:
                    self.log_result("POST /api/rotation/backtest", False, f"Missing metrics: {missing_metrics}")
                    return False
                
                # Check equity curve
                equity_curve = data.get("equity_curve", [])
                if len(equity_curve) == 0:
                    self.log_result("POST /api/rotation/backtest", False, "Empty equity curve")
                    return False
                
                # Success
                total_return = metrics.get("total_return", 0)
                max_dd = metrics.get("max_dd", 0)
                sharpe = metrics.get("sharpe", 0)
                
                self.log_result("POST /api/rotation/backtest", True, 
                              f"Backtest completed: {len(equity_curve)} data points, "
                              f"Return: {total_return:.2%}, Max DD: {max_dd:.2%}, Sharpe: {sharpe:.2f}")
                return True
                
            else:
                self.log_result("POST /api/rotation/backtest", False, f"Status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("POST /api/rotation/backtest", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive rotation lab tests"""
        print("🎯 COMPREHENSIVE ROTATION LAB BACKEND TESTING")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test User: {LOGIN_EMAIL}")
        print("Testing all rotation endpoints as requested in review:")
        print("- Authentication with JWT token extraction")
        print("- GET /api/rotation/config (reported 404 issue)")
        print("- POST /api/rotation/config (reported 404 issue)")
        print("- GET /api/rotation/presets")
        print("- POST /api/rotation/presets")
        print("- DELETE /api/rotation/presets/{name}")
        print("- POST /api/rotation/backtest")
        print("=" * 60)
        
        # Step 1: Authentication
        if not self.authenticate():
            print("\n❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        print("\n⚙️ STEP 2: Rotation Config Endpoints (Critical - reported 404s)")
        # Step 2a: Test GET /api/rotation/config
        self.test_rotation_config_get()
        
        # Step 2b: Test POST /api/rotation/config
        self.test_rotation_config_post()
        
        print("\n📋 STEP 3: Rotation Presets Endpoints")
        # Step 3a: Test GET /api/rotation/presets
        self.test_rotation_presets_get()
        
        # Step 3b: Test POST /api/rotation/presets
        self.test_rotation_presets_post()
        
        # Step 3c: Test DELETE /api/rotation/presets/{name}
        self.test_rotation_presets_delete()
        
        print("\n📊 STEP 4: Rotation Backtest Endpoint")
        # Step 4: Test POST /api/rotation/backtest
        self.test_rotation_backtest()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = sum(1 for result in self.test_results if not result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "0%")
        
        # Critical endpoints check (the ones mentioned in 404 errors)
        critical_endpoints = ["GET /api/rotation/config", "POST /api/rotation/config"]
        critical_passed = 0
        critical_failed = 0
        
        for result in self.test_results:
            if result["test"] in critical_endpoints:
                if result["success"]:
                    critical_passed += 1
                else:
                    critical_failed += 1
        
        print(f"\n🚨 CRITICAL ENDPOINTS (reported 404 errors):")
        print(f"Critical Passed: {critical_passed}/2 ✅")
        print(f"Critical Failed: {critical_failed}/2 ❌")
        
        if critical_failed == 0:
            print("\n🎉 SUCCESS: All critical rotation config endpoints are working!")
            print("✅ The 404 errors reported by the user have been resolved.")
        else:
            print("\n💥 CRITICAL ISSUE: Some rotation config endpoints still failing!")
            print("❌ The 404 errors reported by the user are still present.")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "=" * 60)
        print("🏆 FINAL ASSESSMENT:")
        if failed == 0:
            print("✅ ALL ROTATION LAB ENDPOINTS WORKING PERFECTLY")
            print("✅ No 404 errors found - User's issue has been resolved")
            print("✅ Complete CRUD operations functional")
            print("✅ Backtest engine returning proper results")
        elif critical_failed == 0:
            print("✅ CRITICAL ENDPOINTS WORKING (404 issue resolved)")
            print("⚠️ Some minor issues with other endpoints")
        else:
            print("❌ CRITICAL ENDPOINTS STILL FAILING")
            print("❌ User's 404 errors are still present")
        print("=" * 60)

if __name__ == "__main__":
    tester = ComprehensiveRotationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)