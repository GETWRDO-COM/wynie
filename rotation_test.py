#!/usr/bin/env python3
"""
Rotation Config Endpoints Smoke Test
Tests the specific rotation endpoints as requested in the review
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def test_rotation_endpoints():
    """
    Rotation config endpoints smoke test as requested:
    1) POST /api/auth/login (email=beetge@mwebbiz.co.za, password=Albee1990!) -> token
    2) With token:
       - GET /api/rotation/config -> expect 200 JSON {owner, config}
       - POST /api/rotation/config with config {pairs:[{bull:'TQQQ',bear:'SQQQ',underlying:'QQQ'}]} -> expect 200 saved
       - GET /api/rotation/config -> reflect saved
       - GET /api/rotation/presets -> 200
       - POST /api/rotation/presets -> 200
       - DELETE /api/rotation/presets/{name} -> 200
       - POST /api/rotation/backtest -> 200 with metrics, equity_curve, drawdown
    """
    
    session = requests.Session()
    results = []
    
    def log_result(test_name, success, details=""):
        status = "PASS" if success else "FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        results.append(result)
        print(result)
        return success
    
    try:
        # Step 1: Login
        print("=== ROTATION CONFIG ENDPOINTS SMOKE TEST ===")
        print("1) Testing POST /api/auth/login...")
        
        login_data = {
            "email": "beetge@mwebbiz.co.za",
            "password": "Albee1990!"
        }
        
        login_response = session.post(f"{API_BASE}/auth/login", json=login_data)
        if login_response.status_code != 200:
            log_result("POST /api/auth/login", False, f"HTTP {login_response.status_code}: {login_response.text}")
            return results
        
        login_result = login_response.json()
        if 'access_token' not in login_result:
            log_result("POST /api/auth/login", False, "No access_token in response")
            return results
        
        token = login_result['access_token']
        auth_headers = {"Authorization": f"Bearer {token}"}
        log_result("POST /api/auth/login", True, "Login successful, token received")
        
        # Step 2: GET /api/rotation/config
        print("\n2) Testing GET /api/rotation/config...")
        
        config_response = session.get(f"{API_BASE}/rotation/config", headers=auth_headers)
        if config_response.status_code != 200:
            log_result("GET /api/rotation/config", False, f"HTTP {config_response.status_code}: {config_response.text}")
            return results
        
        config_data = config_response.json()
        if 'owner' not in config_data or 'config' not in config_data:
            log_result("GET /api/rotation/config", False, "Missing owner or config in response")
            return results
        
        log_result("GET /api/rotation/config", True, f"200 JSON with owner: {config_data['owner']}")
        
        # Step 3: POST /api/rotation/config with specific config
        print("\n3) Testing POST /api/rotation/config...")
        
        test_config = {
            "name": "Test Config",
            "capital": 100000.0,
            "rebalance": "D",
            "lookback_days": 126,
            "trend_days": 200,
            "max_positions": 1,
            "cost_bps": 5.0,
            "slippage_bps": 5.0,
            "pairs": [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}],
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
        
        save_config_response = session.post(f"{API_BASE}/rotation/config", json=test_config, headers=auth_headers)
        if save_config_response.status_code != 200:
            log_result("POST /api/rotation/config", False, f"HTTP {save_config_response.status_code}: {save_config_response.text}")
            return results
        
        save_result = save_config_response.json()
        if save_result.get('message') != 'saved':
            log_result("POST /api/rotation/config", False, f"Expected 'saved' message, got: {save_result}")
            return results
        
        log_result("POST /api/rotation/config", True, "200 saved")
        
        # Step 4: GET /api/rotation/config again to verify save
        print("\n4) Testing GET /api/rotation/config (verify saved)...")
        
        verify_response = session.get(f"{API_BASE}/rotation/config", headers=auth_headers)
        if verify_response.status_code != 200:
            log_result("GET /api/rotation/config (verify)", False, f"HTTP {verify_response.status_code}")
            return results
        
        verify_data = verify_response.json()
        saved_pairs = verify_data.get('config', {}).get('pairs', [])
        if not saved_pairs or saved_pairs[0].get('bull') != 'TQQQ':
            log_result("GET /api/rotation/config (verify)", False, "Saved config not reflected correctly")
            return results
        
        log_result("GET /api/rotation/config (verify)", True, "Saved config reflected correctly")
        
        # Step 5: GET /api/rotation/presets
        print("\n5) Testing GET /api/rotation/presets...")
        
        presets_response = session.get(f"{API_BASE}/rotation/presets", headers=auth_headers)
        if presets_response.status_code != 200:
            log_result("GET /api/rotation/presets", False, f"HTTP {presets_response.status_code}: {presets_response.text}")
            return results
        
        presets_data = presets_response.json()
        if 'items' not in presets_data:
            log_result("GET /api/rotation/presets", False, "Missing 'items' in response")
            return results
        
        log_result("GET /api/rotation/presets", True, f"200 with {len(presets_data['items'])} presets")
        
        # Step 6: POST /api/rotation/presets
        print("\n6) Testing POST /api/rotation/presets...")
        
        preset_data = {
            "name": "TestPreset",
            "config": test_config
        }
        
        save_preset_response = session.post(f"{API_BASE}/rotation/presets", json=preset_data, headers=auth_headers)
        if save_preset_response.status_code != 200:
            log_result("POST /api/rotation/presets", False, f"HTTP {save_preset_response.status_code}: {save_preset_response.text}")
            return results
        
        preset_result = save_preset_response.json()
        if preset_result.get('message') != 'saved':
            log_result("POST /api/rotation/presets", False, f"Expected 'saved' message, got: {preset_result}")
            return results
        
        log_result("POST /api/rotation/presets", True, "200 saved")
        
        # Step 7: DELETE /api/rotation/presets/{name}
        print("\n7) Testing DELETE /api/rotation/presets/TestPreset...")
        
        delete_response = session.delete(f"{API_BASE}/rotation/presets/TestPreset", headers=auth_headers)
        if delete_response.status_code != 200:
            log_result("DELETE /api/rotation/presets/{name}", False, f"HTTP {delete_response.status_code}: {delete_response.text}")
            return results
        
        delete_result = delete_response.json()
        if delete_result.get('message') != 'deleted':
            log_result("DELETE /api/rotation/presets/{name}", False, f"Expected 'deleted' message, got: {delete_result}")
            return results
        
        log_result("DELETE /api/rotation/presets/{name}", True, "200 deleted")
        
        # Step 8: POST /api/rotation/backtest
        print("\n8) Testing POST /api/rotation/backtest...")
        
        backtest_config = {
            "pairs": [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}],
            "capital": 100000.0
        }
        
        backtest_response = session.post(f"{API_BASE}/rotation/backtest", json=backtest_config, headers=auth_headers)
        if backtest_response.status_code != 200:
            log_result("POST /api/rotation/backtest", False, f"HTTP {backtest_response.status_code}: {backtest_response.text}")
            return results
        
        backtest_result = backtest_response.json()
        
        # Validate backtest response structure
        required_fields = ['metrics', 'equity_curve', 'drawdown']
        missing_fields = [field for field in required_fields if field not in backtest_result]
        if missing_fields:
            log_result("POST /api/rotation/backtest", False, f"Missing fields: {missing_fields}")
            return results
        
        # Validate metrics
        metrics = backtest_result.get('metrics', {})
        required_metrics = ['cagr', 'max_dd', 'sharpe', 'total_return']
        missing_metrics = [metric for metric in required_metrics if metric not in metrics]
        if missing_metrics:
            log_result("POST /api/rotation/backtest", False, f"Missing metrics: {missing_metrics}")
            return results
        
        # Validate equity curve has data
        equity_curve = backtest_result.get('equity_curve', [])
        if not equity_curve or len(equity_curve) < 100:
            log_result("POST /api/rotation/backtest", False, f"Equity curve too short: {len(equity_curve)} points")
            return results
        
        # Validate drawdown has data
        drawdown = backtest_result.get('drawdown', [])
        if not drawdown or len(drawdown) != len(equity_curve):
            log_result("POST /api/rotation/backtest", False, f"Drawdown length mismatch: {len(drawdown)} vs {len(equity_curve)}")
            return results
        
        log_result("POST /api/rotation/backtest", True, f"200 with metrics, {len(equity_curve)} equity points, {len(drawdown)} drawdown points")
        
        print("\n=== SUMMARY ===")
        passed = sum(1 for r in results if r.startswith("PASS"))
        total = len(results)
        print(f"OVERALL: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎯 ALL ROTATION ENDPOINTS WORKING PERFECTLY!")
            return results
        else:
            print("❌ SOME TESTS FAILED")
            return results
            
    except Exception as e:
        log_result("EXCEPTION", False, f"Unexpected error: {str(e)}")
        return results

if __name__ == "__main__":
    test_rotation_endpoints()