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
            'settings': {'passed': 0, 'failed': 0, 'errors': []},
            'screener_registry': {'passed': 0, 'failed': 0, 'errors': []},
            'screener': {'passed': 0, 'failed': 0, 'errors': []},
            'marketdata': {'passed': 0, 'failed': 0, 'errors': []},
            'watchlists': {'passed': 0, 'failed': 0, 'errors': []},
            'columns': {'passed': 0, 'failed': 0, 'errors': []},
            'ratings': {'passed': 0, 'failed': 0, 'errors': []},
            'websocket': {'passed': 0, 'failed': 0, 'errors': []}
        }
        
    def log_result(self, category, test_name, success, error_msg=None):
        if success:
            self.test_results[category]['passed'] += 1
            print(f"✅ {test_name}")
        else:
            self.test_results[category]['failed'] += 1
            self.test_results[category]['errors'].append(f"{test_name}: {error_msg}")
            print(f"❌ {test_name}: {error_msg}")
    
    def test_settings_endpoints(self):
        print("\n=== Testing Settings Endpoints ===")
        
        # Test 1: GET /api/settings returns booleans
        try:
            response = self.session.get(f"{self.base_url}/api/settings")
            if response.status_code == 200:
                data = response.json()
                if 'polygon' in data and 'finnhub' in data:
                    if isinstance(data['polygon'], bool) and isinstance(data['finnhub'], bool):
                        self.log_result('settings', 'GET /api/settings returns booleans', True)
                    else:
                        self.log_result('settings', 'GET /api/settings returns booleans', False, f"Values are not booleans: polygon={type(data['polygon'])}, finnhub={type(data['finnhub'])}")
                else:
                    self.log_result('settings', 'GET /api/settings returns booleans', False, f"Missing polygon or finnhub keys: {data}")
            else:
                self.log_result('settings', 'GET /api/settings returns booleans', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('settings', 'GET /api/settings returns booleans', False, str(e))
        
        # Test 2: POST /api/settings with new finnhub key
        try:
            # First get current settings
            initial_response = self.session.get(f"{self.base_url}/api/settings")
            initial_data = initial_response.json() if initial_response.status_code == 200 else {}
            
            # Update with new finnhub key
            payload = {"finnhub": "new-test-finnhub-key-123"}
            response = self.session.post(f"{self.base_url}/api/settings", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'ok' in data and data['ok']:
                    # Verify the update worked by checking GET endpoint
                    verify_response = self.session.get(f"{self.base_url}/api/settings")
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        if verify_data.get('finnhub') == True:
                            self.log_result('settings', 'POST /api/settings updates finnhub key and shows finnhub: true', True)
                        else:
                            self.log_result('settings', 'POST /api/settings updates finnhub key and shows finnhub: true', False, f"finnhub not true after update: {verify_data}")
                    else:
                        self.log_result('settings', 'POST /api/settings updates finnhub key and shows finnhub: true', False, f"Failed to verify update: HTTP {verify_response.status_code}")
                else:
                    self.log_result('settings', 'POST /api/settings updates finnhub key and shows finnhub: true', False, f"Invalid response: {data}")
            else:
                self.log_result('settings', 'POST /api/settings updates finnhub key and shows finnhub: true', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('settings', 'POST /api/settings updates finnhub key and shows finnhub: true', False, str(e))
        
        # Test 3: POST /api/settings with polygon key
        try:
            payload = {"polygon": "new-test-polygon-key-456"}
            response = self.session.post(f"{self.base_url}/api/settings", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'ok' in data and data['ok']:
                    self.log_result('settings', 'POST /api/settings updates polygon key', True)
                else:
                    self.log_result('settings', 'POST /api/settings updates polygon key', False, f"Invalid response: {data}")
            else:
                self.log_result('settings', 'POST /api/settings updates polygon key', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('settings', 'POST /api/settings updates polygon key', False, str(e))

    def test_screener_registry(self):
        print("\n=== Testing Screener Registry ===")
        
        # Test 1: GET /api/screeners/filters returns categories and fields including fundamentals
        try:
            response = self.session.get(f"{self.base_url}/api/screeners/filters")
            if response.status_code == 200:
                data = response.json()
                if 'categories' in data and isinstance(data['categories'], list):
                    # Look for fundamentals category with marketCap field
                    fundamentals_found = False
                    marketcap_found = False
                    
                    for category in data['categories']:
                        if category.get('name') == 'Fundamentals':
                            fundamentals_found = True
                            fields = category.get('fields', [])
                            for field in fields:
                                if field.get('id') == 'marketCap':
                                    marketcap_found = True
                                    break
                            break
                    
                    if fundamentals_found and marketcap_found:
                        self.log_result('screener_registry', 'GET /api/screeners/filters returns categories with fundamentals including marketCap', True)
                    else:
                        self.log_result('screener_registry', 'GET /api/screeners/filters returns categories with fundamentals including marketCap', False, f"Missing fundamentals category or marketCap field. Fundamentals found: {fundamentals_found}, MarketCap found: {marketcap_found}")
                else:
                    self.log_result('screener_registry', 'GET /api/screeners/filters returns categories with fundamentals including marketCap', False, f"Invalid response structure: {data}")
            else:
                self.log_result('screener_registry', 'GET /api/screeners/filters returns categories with fundamentals including marketCap', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('screener_registry', 'GET /api/screeners/filters returns categories with fundamentals including marketCap', False, str(e))
        
        # Test 2: Verify all expected categories exist
        try:
            response = self.session.get(f"{self.base_url}/api/screeners/filters")
            if response.status_code == 200:
                data = response.json()
                categories = data.get('categories', [])
                category_names = [cat.get('name') for cat in categories]
                
                expected_categories = ['Price & Volume', 'Technicals', 'Signals', 'Fundamentals']
                missing_categories = [cat for cat in expected_categories if cat not in category_names]
                
                if not missing_categories:
                    self.log_result('screener_registry', 'All expected categories present', True)
                else:
                    self.log_result('screener_registry', 'All expected categories present', False, f"Missing categories: {missing_categories}")
            else:
                self.log_result('screener_registry', 'All expected categories present', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('screener_registry', 'All expected categories present', False, str(e))

    def test_screener_with_fundamentals(self):
        print("\n=== Testing Screener with Fundamentals ===")
        
        # Test 1: Screener run with fundamentals filter (marketCap >= 1B)
        try:
            payload = {
                "symbols": ["AAPL", "MSFT", "TSLA"],
                "filters": [
                    {"field": "marketCap", "op": ">=", "value": 1000000000}
                ]
            }
            response = self.session.post(f"{self.base_url}/api/screeners/run", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'rows' in data and isinstance(data['rows'], list):
                    self.log_result('screener', 'Screener run with marketCap fundamentals filter', True)
                else:
                    self.log_result('screener', 'Screener run with marketCap fundamentals filter', False, f"Missing 'rows' field or invalid structure: {data}")
            else:
                self.log_result('screener', 'Screener run with marketCap fundamentals filter', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('screener', 'Screener run with marketCap fundamentals filter', False, str(e))
        
        # Test 2: Screener with multiple fundamentals filters
        try:
            payload = {
                "symbols": ["AAPL", "MSFT", "TSLA"],
                "filters": [
                    {"field": "marketCap", "op": ">=", "value": 500000000},
                    {"field": "peTTM", "op": "<=", "value": 50}
                ]
            }
            response = self.session.post(f"{self.base_url}/api/screeners/run", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'rows' in data and isinstance(data['rows'], list):
                    self.log_result('screener', 'Screener with multiple fundamentals filters', True)
                else:
                    self.log_result('screener', 'Screener with multiple fundamentals filters', False, f"Invalid response structure: {data}")
            else:
                self.log_result('screener', 'Screener with multiple fundamentals filters', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('screener', 'Screener with multiple fundamentals filters', False, str(e))

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
        
        # Test 2: Bars Data - Test graceful 429 handling
        try:
            response = self.session.get(f"{self.base_url}/api/marketdata/bars?symbol=AAPL&interval=1D")
            if response.status_code == 200:
                data = response.json()
                if 'symbol' in data and 'bars' in data and isinstance(data['bars'], list):
                    # Should return empty bars gracefully on 429, not 500
                    self.log_result('marketdata', 'Bars Data - AAPL 1D (graceful 429 handling)', True)
                else:
                    self.log_result('marketdata', 'Bars Data - AAPL 1D (graceful 429 handling)', False, f"Invalid response structure: {data}")
            else:
                self.log_result('marketdata', 'Bars Data - AAPL 1D (graceful 429 handling)', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('marketdata', 'Bars Data - AAPL 1D (graceful 429 handling)', False, str(e))
        
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
    
    def test_screener_endpoint(self):
        print("\n=== Testing Screener Endpoint ===")
        
        # Test 1: Screener with specific filters and sorting as requested
        try:
            payload = {
                "symbols": ["AAPL", "MSFT", "TSLA", "NVDA"],
                "filters": [
                    {"field": "last", "op": ">=", "value": 5},
                    {"field": "rsi14", "op": ">=", "value": 30}
                ],
                "sort": {"key": "last", "dir": "desc"}
            }
            response = self.session.post(f"{self.base_url}/api/screeners/run", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'rows' in data and isinstance(data['rows'], list):
                    # Validate that rows field exists and has expected structure
                    if len(data['rows']) > 0:
                        # Check if first row has expected fields
                        first_row = data['rows'][0]
                        if 'symbol' in first_row and 'last' in first_row:
                            self.log_result('screener', 'Screener with filters and sort', True)
                        else:
                            self.log_result('screener', 'Screener with filters and sort', False, f"Missing expected fields in row: {first_row}")
                    else:
                        # Empty results are valid if no symbols pass filters
                        self.log_result('screener', 'Screener with filters and sort', True)
                else:
                    self.log_result('screener', 'Screener with filters and sort', False, f"Missing 'rows' field or invalid structure: {data}")
            else:
                self.log_result('screener', 'Screener with filters and sort', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('screener', 'Screener with filters and sort', False, str(e))
        
        # Test 2: Basic screener without filters
        try:
            payload = {
                "symbols": ["AAPL", "MSFT"],
                "filters": []
            }
            response = self.session.post(f"{self.base_url}/api/screeners/run", json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'rows' in data and isinstance(data['rows'], list):
                    self.log_result('screener', 'Basic screener without filters', True)
                else:
                    self.log_result('screener', 'Basic screener without filters', False, f"Invalid response structure: {data}")
            else:
                self.log_result('screener', 'Basic screener without filters', False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result('screener', 'Basic screener without filters', False, str(e))
        
        # Test 3: Error handling - missing symbols
        try:
            payload = {"filters": []}  # Missing symbols
            response = self.session.post(f"{self.base_url}/api/screeners/run", json=payload)
            if response.status_code == 422:  # FastAPI validation error
                self.log_result('screener', 'Error Handling - Missing symbols', True)
            else:
                self.log_result('screener', 'Error Handling - Missing symbols', False, f"Expected 422, got {response.status_code}")
        except Exception as e:
            self.log_result('screener', 'Error Handling - Missing symbols', False, str(e))
    
    def test_websocket_quotes(self):
        print("\n=== Testing WebSocket Quotes ===")
        
        # Test WebSocket connection and message reception
        try:
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://') + '/api/ws/quotes?symbols=AAPL,MSFT'
            
            messages_received = []
            connection_successful = False
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    messages_received.append(data)
                    if len(messages_received) >= 2:  # Stop after receiving 2 messages
                        ws.close()
                except Exception as e:
                    print(f"Error parsing WebSocket message: {e}")
            
            def on_open(ws):
                nonlocal connection_successful
                connection_successful = True
                print("WebSocket connection opened")
            
            def on_error(ws, error):
                print(f"WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                print("WebSocket connection closed")
            
            # Create WebSocket connection
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run WebSocket in a separate thread with timeout
            def run_ws():
                ws.run_forever()
            
            ws_thread = threading.Thread(target=run_ws)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for messages (max 10 seconds)
            timeout = 10
            start_time = time.time()
            while len(messages_received) < 2 and (time.time() - start_time) < timeout:
                time.sleep(0.5)
            
            # Close WebSocket if still open
            try:
                ws.close()
            except:
                pass
            
            # Validate results
            if connection_successful and len(messages_received) > 0:
                # Check message structure
                first_message = messages_received[0]
                if 'type' in first_message and first_message['type'] == 'quotes':
                    if 'data' in first_message and isinstance(first_message['data'], list):
                        # Check if data contains symbol and last fields
                        if len(first_message['data']) > 0:
                            quote = first_message['data'][0]
                            if 'symbol' in quote and 'last' in quote:
                                self.log_result('websocket', 'WebSocket quotes with symbol and last fields', True)
                            else:
                                self.log_result('websocket', 'WebSocket quotes with symbol and last fields', False, f"Missing symbol or last field: {quote}")
                        else:
                            self.log_result('websocket', 'WebSocket quotes with symbol and last fields', False, "Empty data array in WebSocket message")
                    else:
                        self.log_result('websocket', 'WebSocket quotes with symbol and last fields', False, f"Invalid data structure: {first_message}")
                else:
                    self.log_result('websocket', 'WebSocket quotes with symbol and last fields', False, f"Invalid message type: {first_message}")
            else:
                self.log_result('websocket', 'WebSocket quotes with symbol and last fields', False, f"Connection failed or no messages received. Connection: {connection_successful}, Messages: {len(messages_received)}")
                
        except Exception as e:
            self.log_result('websocket', 'WebSocket quotes with symbol and last fields', False, str(e))
    
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
        self.test_screener_endpoint()
        self.test_websocket_quotes()
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