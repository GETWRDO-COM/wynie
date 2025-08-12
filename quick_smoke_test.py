#!/usr/bin/env python3
"""
Quick Backend Smoke Test - Re-validate auth and news endpoints after frontend lint changes
Tests the specific endpoints requested in the review request
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

def test_auth_and_news_endpoints():
    """Test the specific endpoints requested in the review"""
    session = requests.Session()
    results = []
    
    print("🔍 Quick Backend Smoke Test - Re-validating auth and news endpoints")
    print(f"Backend URL: {API_BASE}")
    print("=" * 60)
    
    # 1. POST /api/auth/login with email=beetge@mwebbiz.co.za password=Albee1990! (auto-create or login)
    print("1. Testing POST /api/auth/login...")
    try:
        login_data = {
            "email": "beetge@mwebbiz.co.za",
            "password": "Albee1990!"
        }
        
        login_response = session.post(f"{API_BASE}/auth/login", json=login_data)
        if login_response.status_code == 200:
            login_result = login_response.json()
            if 'access_token' in login_result:
                auth_token = login_result['access_token']
                results.append("✅ PASS: POST /api/auth/login - Login successful, token received")
                print("   ✅ PASS: Login successful, token received")
            else:
                results.append("❌ FAIL: POST /api/auth/login - Missing access_token in response")
                print("   ❌ FAIL: Missing access_token in response")
                return results
        else:
            results.append(f"❌ FAIL: POST /api/auth/login - HTTP {login_response.status_code}: {login_response.text}")
            print(f"   ❌ FAIL: HTTP {login_response.status_code}: {login_response.text}")
            return results
    except Exception as e:
        results.append(f"❌ FAIL: POST /api/auth/login - Error: {str(e)}")
        print(f"   ❌ FAIL: Error: {str(e)}")
        return results
    
    # 2. GET /api/auth/me with token
    print("2. Testing GET /api/auth/me...")
    try:
        auth_headers = {"Authorization": f"Bearer {auth_token}"}
        me_response = session.get(f"{API_BASE}/auth/me", headers=auth_headers)
        
        if me_response.status_code == 200:
            user_info = me_response.json()
            if user_info.get('email') == login_data['email']:
                results.append("✅ PASS: GET /api/auth/me - User info retrieved correctly")
                print("   ✅ PASS: User info retrieved correctly")
            else:
                results.append(f"❌ FAIL: GET /api/auth/me - Email mismatch: {user_info.get('email')} != {login_data['email']}")
                print(f"   ❌ FAIL: Email mismatch: {user_info.get('email')} != {login_data['email']}")
        else:
            results.append(f"❌ FAIL: GET /api/auth/me - HTTP {me_response.status_code}: {me_response.text}")
            print(f"   ❌ FAIL: HTTP {me_response.status_code}: {me_response.text}")
    except Exception as e:
        results.append(f"❌ FAIL: GET /api/auth/me - Error: {str(e)}")
        print(f"   ❌ FAIL: Error: {str(e)}")
    
    # 3. GET /api/news?category=Stock%20Market
    print("3. Testing GET /api/news?category=Stock%20Market...")
    try:
        news_response = session.get(f"{API_BASE}/news?category=Stock%20Market")
        
        if news_response.status_code == 200:
            news_data = news_response.json()
            if 'items' in news_data and len(news_data['items']) > 0:
                item_count = len(news_data['items'])
                results.append(f"✅ PASS: GET /api/news?category=Stock%20Market - {item_count} news items returned")
                print(f"   ✅ PASS: {item_count} news items returned")
            else:
                results.append("❌ FAIL: GET /api/news?category=Stock%20Market - No news items returned")
                print("   ❌ FAIL: No news items returned")
        else:
            results.append(f"❌ FAIL: GET /api/news?category=Stock%20Market - HTTP {news_response.status_code}: {news_response.text}")
            print(f"   ❌ FAIL: HTTP {news_response.status_code}: {news_response.text}")
    except Exception as e:
        results.append(f"❌ FAIL: GET /api/news?category=Stock%20Market - Error: {str(e)}")
        print(f"   ❌ FAIL: Error: {str(e)}")
    
    # 4. GET /api/greed-fear
    print("4. Testing GET /api/greed-fear...")
    try:
        greed_fear_response = session.get(f"{API_BASE}/greed-fear")
        
        if greed_fear_response.status_code == 200:
            greed_fear_data = greed_fear_response.json()
            if 'now' in greed_fear_data and 'last_updated' in greed_fear_data:
                fear_greed_score = greed_fear_data['now']
                if 0 <= fear_greed_score <= 100:
                    results.append(f"✅ PASS: GET /api/greed-fear - Score: {fear_greed_score} (valid 0-100 range)")
                    print(f"   ✅ PASS: Score: {fear_greed_score} (valid 0-100 range)")
                else:
                    results.append(f"❌ FAIL: GET /api/greed-fear - Score {fear_greed_score} out of 0-100 range")
                    print(f"   ❌ FAIL: Score {fear_greed_score} out of 0-100 range")
            else:
                results.append("❌ FAIL: GET /api/greed-fear - Missing 'now' or 'last_updated' fields")
                print("   ❌ FAIL: Missing 'now' or 'last_updated' fields")
        else:
            results.append(f"❌ FAIL: GET /api/greed-fear - HTTP {greed_fear_response.status_code}: {greed_fear_response.text}")
            print(f"   ❌ FAIL: HTTP {greed_fear_response.status_code}: {greed_fear_response.text}")
    except Exception as e:
        results.append(f"❌ FAIL: GET /api/greed-fear - Error: {str(e)}")
        print(f"   ❌ FAIL: Error: {str(e)}")
    
    # 5. GET /api/market/aggregates
    print("5. Testing GET /api/market/aggregates...")
    try:
        aggregates_response = session.get(f"{API_BASE}/market/aggregates")
        
        if aggregates_response.status_code == 200:
            aggregates_data = aggregates_response.json()
            expected_tickers = ['SPY', 'QQQ', 'I:DJI', 'TQQQ', 'SQQQ']
            
            if 'data' in aggregates_data:
                tickers_data = aggregates_data['data']
                found_tickers = list(tickers_data.keys())
                missing_tickers = [ticker for ticker in expected_tickers if ticker not in found_tickers]
                
                if not missing_tickers:
                    results.append(f"✅ PASS: GET /api/market/aggregates - All 5 tickers present: {found_tickers}")
                    print(f"   ✅ PASS: All 5 tickers present: {found_tickers}")
                else:
                    results.append(f"❌ FAIL: GET /api/market/aggregates - Missing tickers: {missing_tickers}")
                    print(f"   ❌ FAIL: Missing tickers: {missing_tickers}")
            else:
                results.append("❌ FAIL: GET /api/market/aggregates - Missing 'data' field")
                print("   ❌ FAIL: Missing 'data' field")
        else:
            results.append(f"❌ FAIL: GET /api/market/aggregates - HTTP {aggregates_response.status_code}: {aggregates_response.text}")
            print(f"   ❌ FAIL: HTTP {aggregates_response.status_code}: {aggregates_response.text}")
    except Exception as e:
        results.append(f"❌ FAIL: GET /api/market/aggregates - Error: {str(e)}")
        print(f"   ❌ FAIL: Error: {str(e)}")
    
    # 6. GET /api/market-score
    print("6. Testing GET /api/market-score...")
    try:
        market_score_response = session.get(f"{API_BASE}/market-score")
        
        if market_score_response.status_code == 200:
            market_score_data = market_score_response.json()
            if 'total_score' in market_score_data and 'classification' in market_score_data:
                total_score = market_score_data['total_score']
                classification = market_score_data['classification']
                results.append(f"✅ PASS: GET /api/market-score - Score: {total_score}, Classification: {classification}")
                print(f"   ✅ PASS: Score: {total_score}, Classification: {classification}")
            else:
                results.append("❌ FAIL: GET /api/market-score - Missing 'total_score' or 'classification' fields")
                print("   ❌ FAIL: Missing 'total_score' or 'classification' fields")
        else:
            results.append(f"❌ FAIL: GET /api/market-score - HTTP {market_score_response.status_code}: {market_score_response.text}")
            print(f"   ❌ FAIL: HTTP {market_score_response.status_code}: {market_score_response.text}")
    except Exception as e:
        results.append(f"❌ FAIL: GET /api/market-score - Error: {str(e)}")
        print(f"   ❌ FAIL: Error: {str(e)}")
    
    return results

if __name__ == "__main__":
    results = test_auth_and_news_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 QUICK SMOKE TEST RESULTS:")
    print("=" * 60)
    
    pass_count = sum(1 for result in results if result.startswith("✅"))
    fail_count = sum(1 for result in results if result.startswith("❌"))
    
    for result in results:
        print(result)
    
    print("\n" + "=" * 60)
    if fail_count == 0:
        print(f"🎉 ALL TESTS PASSED ({pass_count}/{len(results)})")
        print("✅ Backend endpoints are stable after frontend lint changes")
    else:
        print(f"⚠️  SOME TESTS FAILED ({pass_count} passed, {fail_count} failed)")
        print("❌ Issues found that need attention")
    print("=" * 60)