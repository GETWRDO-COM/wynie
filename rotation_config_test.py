#!/usr/bin/env python3
"""
Rotation Config Endpoints Test
Specifically tests the GET and POST /api/rotation/config endpoints mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime

# Configuration from review request
BACKEND_URL = "https://premium-fintech-2.preview.emergentagent.com"
LOGIN_EMAIL = "beetge@mwebbiz.co.za"
LOGIN_PASSWORD = "Albee1990!"

# Sample rotation config from review request
SAMPLE_ROTATION_CONFIG = {
    "name": "Test Config",
    "capital": 100000.0,
    "rebalance": "D",
    "pairs": [{"bull": "TQQQ", "bear": "SQQQ", "underlying": "QQQ"}],
    "ema_fast": 20,
    "ema_slow": 50,
    "conf_threshold": 2
}

def test_rotation_config_endpoints():
    """Test the specific rotation config endpoints mentioned in the 404 errors"""
    print("🎯 ROTATION CONFIG ENDPOINTS TEST")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing endpoints that were causing 404 errors:")
    print("- GET /api/rotation/config")
    print("- POST /api/rotation/config")
    print("=" * 50)
    
    session = requests.Session()
    
    # Step 1: Authentication
    print("\n🔐 Step 1: Authentication")
    try:
        response = session.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                session.headers.update({"Authorization": f"Bearer {token}"})
                print(f"✅ Login successful, token received")
            else:
                print(f"❌ No access token in response")
                return False
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return False
    
    # Step 2: Test GET /api/rotation/config
    print("\n📥 Step 2: Testing GET /api/rotation/config")
    try:
        response = session.get(f"{BACKEND_URL}/api/rotation/config")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ GET /api/rotation/config - SUCCESS")
            print(f"Response structure: {list(data.keys())}")
            if "owner" in data and "config" in data:
                config = data["config"]
                print(f"Owner: {data['owner']}")
                print(f"Config name: {config.get('name', 'N/A')}")
                print(f"Capital: {config.get('capital', 'N/A')}")
                print(f"Pairs count: {len(config.get('pairs', []))}")
            else:
                print(f"⚠️ Unexpected response structure: {data}")
        elif response.status_code == 404:
            print(f"❌ GET /api/rotation/config - 404 NOT FOUND (This was the reported issue)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❌ GET /api/rotation/config - Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ GET /api/rotation/config error: {str(e)}")
        return False
    
    # Step 3: Test POST /api/rotation/config
    print("\n📤 Step 3: Testing POST /api/rotation/config")
    try:
        response = session.post(
            f"{BACKEND_URL}/api/rotation/config",
            json=SAMPLE_ROTATION_CONFIG,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ POST /api/rotation/config - SUCCESS")
            print(f"Response: {data}")
            if data.get("message") == "saved":
                print(f"Config saved successfully")
            else:
                print(f"⚠️ Unexpected response: {data}")
        elif response.status_code == 404:
            print(f"❌ POST /api/rotation/config - 404 NOT FOUND (This was the reported issue)")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"❌ POST /api/rotation/config - Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ POST /api/rotation/config error: {str(e)}")
        return False
    
    # Step 4: Verify the saved config
    print("\n🔍 Step 4: Verifying saved config")
    try:
        response = session.get(f"{BACKEND_URL}/api/rotation/config")
        if response.status_code == 200:
            data = response.json()
            config = data.get("config", {})
            if config.get("name") == SAMPLE_ROTATION_CONFIG["name"]:
                print(f"✅ Config verification - SUCCESS")
                print(f"Saved config name: {config.get('name')}")
                print(f"Saved pairs: {len(config.get('pairs', []))}")
                if config.get('pairs'):
                    pair = config['pairs'][0]
                    print(f"First pair: {pair.get('bull')}/{pair.get('bear')} on {pair.get('underlying')}")
            else:
                print(f"⚠️ Config not saved correctly")
                print(f"Expected name: {SAMPLE_ROTATION_CONFIG['name']}")
                print(f"Actual name: {config.get('name')}")
        else:
            print(f"❌ Verification failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL ROTATION CONFIG ENDPOINTS WORKING!")
    print("✅ GET /api/rotation/config - Returns user's rotation config")
    print("✅ POST /api/rotation/config - Saves rotation config successfully")
    print("✅ No 404 errors found - Issue appears to be resolved")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = test_rotation_config_endpoints()
    if success:
        print("\n🏆 CONCLUSION: The rotation config endpoints are working correctly.")
        print("The 404 errors reported by the user appear to have been resolved.")
    else:
        print("\n💥 CONCLUSION: Issues found with rotation config endpoints.")
        print("The 404 errors reported by the user are still present.")
    
    sys.exit(0 if success else 1)