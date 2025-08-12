#!/usr/bin/env python3
"""
Focused test for screener expansion features
"""

import requests
import json
import sys

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

print(f"Testing screener expansion at: {BASE_URL}")

session = requests.Session()

def test_settings():
    print("\n=== Testing Settings (API Keys) ===")
    try:
        response = session.get(f"{BASE_URL}/api/settings")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Settings: polygon={data.get('polygon')}, finnhub={data.get('finnhub')}")
            return data.get('polygon') and data.get('finnhub')
        else:
            print(f"❌ Settings failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def test_screener_filters():
    print("\n=== Testing Screener Filters (New Fields) ===")
    try:
        response = session.get(f"{BASE_URL}/api/screeners/filters")
        if response.status_code == 200:
            data = response.json()
            categories = data.get('categories', [])
            
            # Check for new fields
            new_fields = ['macd_line', 'macd_signal', 'macd_hist', 'stoch_k', 'stoch_d', 'gapPct', 'liquidity', 'hi52', 'lo52']
            found_fields = []
            
            for category in categories:
                fields = category.get('fields', [])
                for field in fields:
                    field_id = field.get('id')
                    if field_id in new_fields:
                        found_fields.append(field_id)
            
            missing_fields = [f for f in new_fields if f not in found_fields]
            if not missing_fields:
                print(f"✅ All new fields found: {found_fields}")
                return True
            else:
                print(f"❌ Missing fields: {missing_fields}")
                return False
        else:
            print(f"❌ Filters failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Filters error: {e}")
        return False

def test_screener_runs():
    print("\n=== Testing Screener Runs (Specific Cases) ===")
    universe = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "GOOGL", "META", "AMD", "NFLX", "AVGO"]
    
    test_cases = [
        {
            "name": "pct_to_hi52 <= 2 sorted by last desc",
            "payload": {
                "symbols": universe,
                "filters": [{"field": "pct_to_hi52", "op": "<=", "value": 2}],
                "sort": {"key": "last", "dir": "desc"}
            }
        },
        {
            "name": "relVol >= 1.2",
            "payload": {
                "symbols": universe,
                "filters": [{"field": "relVol", "op": ">=", "value": 1.2}]
            }
        },
        {
            "name": "macd_cross_up == true",
            "payload": {
                "symbols": universe,
                "filters": [{"field": "macd_cross_up", "op": "==", "value": True}]
            }
        },
        {
            "name": "AND group (marketCap >= 1B AND rsi14 between [30,70])",
            "payload": {
                "symbols": universe,
                "filters": [{
                    "logic": "AND",
                    "filters": [
                        {"field": "marketCap", "op": ">=", "value": 1000000000},
                        {"field": "rsi14", "op": "between", "value": [30, 70]}
                    ]
                }]
            }
        }
    ]
    
    results = []
    for test_case in test_cases:
        try:
            response = session.post(f"{BASE_URL}/api/screeners/run", json=test_case["payload"])
            if response.status_code == 200:
                data = response.json()
                if 'rows' in data and 'nextCursor' in data:
                    print(f"✅ {test_case['name']}: {len(data['rows'])} rows returned")
                    results.append(True)
                else:
                    print(f"❌ {test_case['name']}: Invalid response structure")
                    results.append(False)
            else:
                print(f"❌ {test_case['name']}: HTTP {response.status_code}")
                if response.status_code == 500:
                    print(f"   Response: {response.text}")
                results.append(False)
        except Exception as e:
            print(f"❌ {test_case['name']}: {e}")
            results.append(False)
    
    return all(results)

if __name__ == "__main__":
    print("=== SCREENER EXPANSION TESTING ===")
    
    # Test API keys first
    settings_ok = test_settings()
    if not settings_ok:
        print("⚠️  API keys not properly configured, some tests may fail")
    
    # Test new fields in registry
    filters_ok = test_screener_filters()
    
    # Test screener runs with new fields
    runs_ok = test_screener_runs()
    
    print("\n=== SUMMARY ===")
    print(f"Settings (API Keys): {'✅' if settings_ok else '❌'}")
    print(f"New Fields in Registry: {'✅' if filters_ok else '❌'}")
    print(f"Screener Runs: {'✅' if runs_ok else '❌'}")
    
    if settings_ok and filters_ok and runs_ok:
        print("🎉 ALL SCREENER EXPANSION TESTS PASSED!")
    else:
        print("⚠️  Some tests failed - check details above")