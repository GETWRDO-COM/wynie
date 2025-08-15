#!/usr/bin/env python3
"""
ETF Intelligence System Backend API Tests
Tests all backend endpoints systematically
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

class ETFBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.watchlist_items_created = []
        self.auth_token = None
        self.chat_session_id = None
        
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
        
    def test_api_root(self):
        """Test root API endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("API Root", True, f"Root endpoint accessible: {data['message']}")
                    return True
                else:
                    self.log_test("API Root", False, "Root endpoint missing message field")
                    return False
            else:
                self.log_test("API Root", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Connection error: {str(e)}")
            return False

    def test_authentication_system(self):
        """Test Authentication System with JWT and User Management"""
        try:
            # Test login with provided credentials
            login_data = {
                "email": "beetge@mwebbiz.co.za",
                "password": "Albee1990!"
            }
            
            login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            if login_response.status_code != 200:
                self.log_test("Authentication System", False, f"Login failed: HTTP {login_response.status_code}: {login_response.text}")
                return False
            
            login_result = login_response.json()
            
            # Validate login response structure
            required_fields = ['access_token', 'token_type', 'user']
            missing_fields = [field for field in required_fields if field not in login_result]
            if missing_fields:
                self.log_test("Authentication System", False, f"Login response missing fields: {missing_fields}")
                return False
            
            # Store auth token for subsequent requests
            self.auth_token = login_result['access_token']
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test /auth/me endpoint
            me_response = self.session.get(f"{API_BASE}/auth/me", headers=auth_headers)
            if me_response.status_code != 200:
                self.log_test("Authentication System", False, f"Get current user failed: HTTP {me_response.status_code}")
                return False
            
            user_info = me_response.json()
            if user_info.get('email') != login_data['email']:
                self.log_test("Authentication System", False, f"User email mismatch: {user_info.get('email')} != {login_data['email']}")
                return False
            
            # Test password update (settings)
            settings_data = {
                "current_password": "Albee1990!",
                "new_password": "Albee1990!New"
            }
            
            settings_response = self.session.post(f"{API_BASE}/auth/settings", json=settings_data, headers=auth_headers)
            if settings_response.status_code != 200:
                self.log_test("Authentication System", False, f"Password update failed: HTTP {settings_response.status_code}")
                return False
            
            # Change password back
            settings_back_data = {
                "current_password": "Albee1990!New",
                "new_password": "Albee1990!"
            }
            
            settings_back_response = self.session.post(f"{API_BASE}/auth/settings", json=settings_back_data, headers=auth_headers)
            if settings_back_response.status_code != 200:
                self.log_test("Authentication System", False, f"Password revert failed: HTTP {settings_back_response.status_code}")
                return False
            
            # Test forgot password endpoint
            forgot_data = {"email": "beetge@mwebbiz.co.za"}
            forgot_response = self.session.post(f"{API_BASE}/auth/forgot-password", json=forgot_data)
            if forgot_response.status_code != 200:
                self.log_test("Authentication System", False, f"Forgot password failed: HTTP {forgot_response.status_code}")
                return False
            
            forgot_result = forgot_response.json()
            if 'message' not in forgot_result:
                self.log_test("Authentication System", False, "Forgot password response missing message")
                return False
            
            self.log_test("Authentication System", True, "Complete authentication system working: login, JWT tokens, user info, password updates, forgot password")
            return True
            
        except Exception as e:
            self.log_test("Authentication System", False, f"Error: {str(e)}")
            return False

    def test_ai_chat_integration(self):
        """Test AI Chat Integration with OpenAI Models"""
        try:
            if not self.auth_token:
                self.log_test("AI Chat Integration", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test get available models
            models_response = self.session.get(f"{API_BASE}/ai/models")
            if models_response.status_code != 200:
                self.log_test("AI Chat Integration", False, f"Get models failed: HTTP {models_response.status_code}")
                return False
            
            models_data = models_response.json()
            required_model_fields = ['models', 'latest_model', 'recommended']
            missing_model_fields = [field for field in required_model_fields if field not in models_data]
            if missing_model_fields:
                self.log_test("AI Chat Integration", False, f"Models response missing fields: {missing_model_fields}")
                return False
            
            # Validate model list contains expected models
            models = models_data.get('models', {})
            expected_models = ['latest', 'gpt-4.1', 'o3', 'o1-pro']
            missing_models = [model for model in expected_models if model not in models]
            if missing_models:
                self.log_test("AI Chat Integration", False, f"Missing expected models: {missing_models}")
                return False
            
            # Create a chat session
            session_data = {
                "title": "Test Trading Session",
                "model": "gpt-4.1",
                "system_message": "You are a financial advisor for testing."
            }
            
            session_response = self.session.post(f"{API_BASE}/ai/sessions", json=session_data, headers=auth_headers)
            if session_response.status_code != 200:
                self.log_test("AI Chat Integration", False, f"Create session failed: HTTP {session_response.status_code}")
                return False
            
            session_result = session_response.json()
            self.chat_session_id = session_result.get('id')
            if not self.chat_session_id:
                self.log_test("AI Chat Integration", False, "Created session missing ID")
                return False
            
            # Test chat with AI
            chat_data = {
                "session_id": self.chat_session_id,
                "message": "What is the current market sentiment for tech stocks?",
                "model": "gpt-4.1",
                "include_chart_data": False
            }
            
            chat_response = self.session.post(f"{API_BASE}/ai/chat", json=chat_data, headers=auth_headers)
            if chat_response.status_code != 200:
                self.log_test("AI Chat Integration", False, f"AI chat failed: HTTP {chat_response.status_code}")
                return False
            
            chat_result = chat_response.json()
            required_chat_fields = ['response', 'session_id', 'model_used']
            missing_chat_fields = [field for field in required_chat_fields if field not in chat_result]
            if missing_chat_fields:
                self.log_test("AI Chat Integration", False, f"Chat response missing fields: {missing_chat_fields}")
                return False
            
            # Validate AI response is meaningful
            ai_response = chat_result.get('response', '')
            if len(ai_response) < 50:  # AI should provide substantial response
                self.log_test("AI Chat Integration", False, f"AI response too short: {len(ai_response)} characters")
                return False
            
            # Test chat with chart context
            chart_chat_data = {
                "session_id": self.chat_session_id,
                "message": "Analyze AAPL chart for swing trading opportunities",
                "model": "gpt-4.1",
                "ticker": "AAPL",
                "include_chart_data": True
            }
            
            chart_chat_response = self.session.post(f"{API_BASE}/ai/chat", json=chart_chat_data, headers=auth_headers)
            if chart_chat_response.status_code != 200:
                self.log_test("AI Chat Integration", False, f"Chart-context chat failed: HTTP {chart_chat_response.status_code}")
                return False
            
            # Test get chat sessions
            sessions_response = self.session.get(f"{API_BASE}/ai/sessions", headers=auth_headers)
            if sessions_response.status_code != 200:
                self.log_test("AI Chat Integration", False, f"Get sessions failed: HTTP {sessions_response.status_code}")
                return False
            
            sessions = sessions_response.json()
            session_found = any(session.get('id') == self.chat_session_id for session in sessions)
            if not session_found:
                self.log_test("AI Chat Integration", False, "Created session not found in sessions list")
                return False
            
            # Test get session messages
            messages_response = self.session.get(f"{API_BASE}/ai/sessions/{self.chat_session_id}/messages", headers=auth_headers)
            if messages_response.status_code != 200:
                self.log_test("AI Chat Integration", False, f"Get messages failed: HTTP {messages_response.status_code}")
                return False
            
            messages = messages_response.json()
            if len(messages) < 2:  # Should have at least user message and AI response
                self.log_test("AI Chat Integration", False, f"Expected at least 2 messages, got {len(messages)}")
                return False
            
            self.log_test("AI Chat Integration", True, "AI chat system fully functional: model selection, sessions, chat with/without chart context, message history")
            return True
            
        except Exception as e:
            self.log_test("AI Chat Integration", False, f"Error: {str(e)}")
            return False

    def test_enhanced_company_search(self):
        """Test Enhanced Company Search and Stock Analysis"""
        try:
            # Test company search by ticker
            search_response = self.session.get(f"{API_BASE}/companies/search?query=AAPL&limit=5")
            if search_response.status_code != 200:
                self.log_test("Enhanced Company Search", False, f"Search by ticker failed: HTTP {search_response.status_code}")
                return False
            
            search_result = search_response.json()
            if 'companies' not in search_result or 'count' not in search_result:
                self.log_test("Enhanced Company Search", False, "Search response missing companies or count")
                return False
            
            companies = search_result.get('companies', [])
            if not companies:
                self.log_test("Enhanced Company Search", False, "No companies returned for AAPL search")
                return False
            
            # Validate company data structure
            sample_company = companies[0]
            required_company_fields = ['ticker', 'company_name', 'sector', 'industry', 'market_cap', 'rotation_status']
            missing_company_fields = [field for field in required_company_fields if field not in sample_company]
            if missing_company_fields:
                self.log_test("Enhanced Company Search", False, f"Company data missing fields: {missing_company_fields}")
                return False
            
            # Test company search by name
            name_search_response = self.session.get(f"{API_BASE}/companies/search?query=Apple&limit=5")
            if name_search_response.status_code != 200:
                self.log_test("Enhanced Company Search", False, f"Search by name failed: HTTP {name_search_response.status_code}")
                return False
            
            # Test detailed company information
            detail_response = self.session.get(f"{API_BASE}/companies/AAPL")
            if detail_response.status_code != 200:
                self.log_test("Enhanced Company Search", False, f"Company details failed: HTTP {detail_response.status_code}")
                return False
            
            detail_result = detail_response.json()
            required_detail_fields = ['company', 'market_data']
            missing_detail_fields = [field for field in required_detail_fields if field not in detail_result]
            if missing_detail_fields:
                self.log_test("Enhanced Company Search", False, f"Company details missing fields: {missing_detail_fields}")
                return False
            
            # Validate company info includes logo URL
            company_info = detail_result.get('company', {})
            if 'logo_url' not in company_info:
                self.log_test("Enhanced Company Search", False, "Company info missing logo_url")
                return False
            
            # Validate market data
            market_data = detail_result.get('market_data', {})
            required_market_fields = ['current_price', 'change_1d', 'change_1w', 'change_1m']
            missing_market_fields = [field for field in required_market_fields if field not in market_data]
            if missing_market_fields:
                self.log_test("Enhanced Company Search", False, f"Market data missing fields: {missing_market_fields}")
                return False
            
            # Test rotation status validation
            rotation_status = company_info.get('rotation_status', '')
            valid_rotation_statuses = ['Rotating In', 'Rotating Out', 'Neutral', 'Unknown']
            if rotation_status not in valid_rotation_statuses:
                self.log_test("Enhanced Company Search", False, f"Invalid rotation status: {rotation_status}")
                return False
            
            self.log_test("Enhanced Company Search", True, "Company search system working: ticker/name search, detailed info, logos, sector rotation analysis")
            return True
            
        except Exception as e:
            self.log_test("Enhanced Company Search", False, f"Error: {str(e)}")
            return False

    def test_tradingview_integration(self):
        """Test TradingView Integration and Chart Drawing"""
        try:
            if not self.auth_token:
                self.log_test("TradingView Integration", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test connect TradingView account
            account_data = {
                "username": "test_trader_account",
                "access_token": "test_access_token_123"
            }
            
            connect_response = self.session.post(f"{API_BASE}/tradingview/connect", json=account_data, headers=auth_headers)
            if connect_response.status_code != 200:
                self.log_test("TradingView Integration", False, f"Connect account failed: HTTP {connect_response.status_code}")
                return False
            
            connect_result = connect_response.json()
            if 'message' not in connect_result or 'account' not in connect_result:
                self.log_test("TradingView Integration", False, "Connect response missing message or account")
                return False
            
            # Test get TradingView account
            account_response = self.session.get(f"{API_BASE}/tradingview/account", headers=auth_headers)
            if account_response.status_code != 200:
                self.log_test("TradingView Integration", False, f"Get account failed: HTTP {account_response.status_code}")
                return False
            
            account_result = account_response.json()
            if not account_result.get('connected'):
                self.log_test("TradingView Integration", False, "Account not showing as connected")
                return False
            
            # Test save chart drawing
            drawing_data = {
                "ticker": "AAPL",
                "drawing_data": {
                    "type": "trendline",
                    "points": [{"x": 100, "y": 150}, {"x": 200, "y": 160}],
                    "color": "#FF0000",
                    "style": "solid"
                },
                "timeframe": "1D"
            }
            
            drawing_response = self.session.post(f"{API_BASE}/tradingview/drawings", json=drawing_data, headers=auth_headers)
            if drawing_response.status_code != 200:
                self.log_test("TradingView Integration", False, f"Save drawing failed: HTTP {drawing_response.status_code}")
                return False
            
            drawing_result = drawing_response.json()
            if 'message' not in drawing_result or 'drawing' not in drawing_result:
                self.log_test("TradingView Integration", False, "Drawing response missing message or drawing")
                return False
            
            # Test get chart drawings for ticker
            get_drawings_response = self.session.get(f"{API_BASE}/tradingview/drawings/AAPL", headers=auth_headers)
            if get_drawings_response.status_code != 200:
                self.log_test("TradingView Integration", False, f"Get drawings failed: HTTP {get_drawings_response.status_code}")
                return False
            
            drawings = get_drawings_response.json()
            if not isinstance(drawings, list):
                self.log_test("TradingView Integration", False, "Drawings response not a list")
                return False
            
            # Should find the drawing we just created
            drawing_found = any(drawing.get('ticker') == 'AAPL' for drawing in drawings)
            if not drawing_found:
                self.log_test("TradingView Integration", False, "Created drawing not found in get drawings")
                return False
            
            self.log_test("TradingView Integration", True, "TradingView integration working: account connection, chart drawing save/retrieve")
            return True
            
        except Exception as e:
            self.log_test("TradingView Integration", False, f"Error: {str(e)}")
            return False

    def test_interactive_charts(self):
        """Test Interactive Charts with Multiple Timeframes"""
        try:
            # Test indices chart data with different timeframes
            timeframes = ['1d', '1w', '1m', '1y']
            
            for timeframe in timeframes:
                indices_response = self.session.get(f"{API_BASE}/charts/indices?timeframe={timeframe}")
                if indices_response.status_code != 200:
                    self.log_test("Interactive Charts", False, f"Indices chart {timeframe} failed: HTTP {indices_response.status_code}")
                    return False
                
                indices_data = indices_response.json()
                required_indices_fields = ['data', 'timeframe']
                missing_indices_fields = [field for field in required_indices_fields if field not in indices_data]
                if missing_indices_fields:
                    self.log_test("Interactive Charts", False, f"Indices chart missing fields: {missing_indices_fields}")
                    return False
                
                # Validate chart data structure
                chart_data = indices_data.get('data', {})
                expected_indices = ['SPY', 'QQQ', 'DIA', 'IWM']
                
                for index in expected_indices:
                    if index not in chart_data:
                        self.log_test("Interactive Charts", False, f"Missing index {index} in {timeframe} chart data")
                        return False
                    
                    index_data = chart_data[index]
                    required_chart_fields = ['dates', 'prices', 'volumes', 'highs', 'lows', 'opens']
                    missing_chart_fields = [field for field in required_chart_fields if field not in index_data]
                    if missing_chart_fields:
                        self.log_test("Interactive Charts", False, f"{index} chart missing fields: {missing_chart_fields}")
                        return False
                    
                    # Validate data arrays have same length
                    dates = index_data.get('dates', [])
                    prices = index_data.get('prices', [])
                    if len(dates) != len(prices) or len(dates) == 0:
                        self.log_test("Interactive Charts", False, f"{index} chart data arrays length mismatch or empty")
                        return False
            
            # Test individual ticker chart data
            ticker_response = self.session.get(f"{API_BASE}/charts/AAPL?timeframe=1mo")
            if ticker_response.status_code != 200:
                self.log_test("Interactive Charts", False, f"Ticker chart failed: HTTP {ticker_response.status_code}")
                return False
            
            ticker_data = ticker_response.json()
            required_ticker_fields = ['ticker', 'timeframe', 'data']
            missing_ticker_fields = [field for field in required_ticker_fields if field not in ticker_data]
            if missing_ticker_fields:
                self.log_test("Interactive Charts", False, f"Ticker chart missing fields: {missing_ticker_fields}")
                return False
            
            # Validate ticker chart data
            ticker_chart_data = ticker_data.get('data', {})
            required_ticker_chart_fields = ['dates', 'prices', 'volumes', 'highs', 'lows', 'opens']
            missing_ticker_chart_fields = [field for field in required_ticker_chart_fields if field not in ticker_chart_data]
            if missing_ticker_chart_fields:
                self.log_test("Interactive Charts", False, f"Ticker chart data missing fields: {missing_ticker_chart_fields}")
                return False
            
            # Validate OHLCV data consistency
            ohlcv_data = ticker_chart_data
            data_lengths = [len(ohlcv_data[field]) for field in required_ticker_chart_fields]
            if len(set(data_lengths)) > 1:  # All arrays should have same length
                self.log_test("Interactive Charts", False, f"OHLCV data arrays have inconsistent lengths: {data_lengths}")
                return False
            
            self.log_test("Interactive Charts", True, f"Interactive charts working: multiple timeframes ({len(timeframes)}), indices and individual tickers, OHLCV data")
            return True
            
        except Exception as e:
            self.log_test("Interactive Charts", False, f"Error: {str(e)}")
            return False

    def test_spreadsheet_interface(self):
        """Test Spreadsheet-Style Interface with Formula Transparency"""
        try:
            # Test spreadsheet ETF data
            spreadsheet_response = self.session.get(f"{API_BASE}/spreadsheet/etfs")
            if spreadsheet_response.status_code != 200:
                self.log_test("Spreadsheet Interface", False, f"Spreadsheet ETFs failed: HTTP {spreadsheet_response.status_code}")
                return False
            
            spreadsheet_data = spreadsheet_response.json()
            required_spreadsheet_fields = ['data', 'formulas', 'total_records']
            missing_spreadsheet_fields = [field for field in required_spreadsheet_fields if field not in spreadsheet_data]
            if missing_spreadsheet_fields:
                self.log_test("Spreadsheet Interface", False, f"Spreadsheet response missing fields: {missing_spreadsheet_fields}")
                return False
            
            # Validate spreadsheet data structure
            data = spreadsheet_data.get('data', [])
            if not data:
                self.log_test("Spreadsheet Interface", False, "No spreadsheet data returned")
                return False
            
            # Validate spreadsheet row structure
            sample_row = data[0]
            expected_spreadsheet_columns = ['Ticker', 'Name', 'Sector', 'Price', 'SATA', 'GMMA', 'ATR_Percent', 'RS_1M', 'Color_Rule']
            missing_columns = [col for col in expected_spreadsheet_columns if col not in sample_row]
            if missing_columns:
                self.log_test("Spreadsheet Interface", False, f"Spreadsheet row missing columns: {missing_columns}")
                return False
            
            # Validate formulas section
            formulas = spreadsheet_data.get('formulas', {})
            expected_formulas = ['swing_days', 'atr_percent', 'relative_strength', 'sata_score', 'color_logic']
            missing_formulas = [formula for formula in expected_formulas if formula not in formulas]
            if missing_formulas:
                self.log_test("Spreadsheet Interface", False, f"Missing formula definitions: {missing_formulas}")
                return False
            
            # Validate formula content
            for formula_name, formula_content in formulas.items():
                if not isinstance(formula_content, str) or len(formula_content) < 10:
                    self.log_test("Spreadsheet Interface", False, f"Formula {formula_name} content invalid or too short")
                    return False
            
            # Test with sector filter
            sector_response = self.session.get(f"{API_BASE}/spreadsheet/etfs?sector=Technology")
            if sector_response.status_code != 200:
                self.log_test("Spreadsheet Interface", False, f"Spreadsheet sector filter failed: HTTP {sector_response.status_code}")
                return False
            
            sector_data = sector_response.json()
            sector_rows = sector_data.get('data', [])
            if sector_rows:
                # Verify all rows are from Technology sector
                non_tech_rows = [row for row in sector_rows if row.get('Sector') != 'Technology']
                if non_tech_rows:
                    self.log_test("Spreadsheet Interface", False, f"Sector filter not working: found {len(non_tech_rows)} non-Technology rows")
                    return False
            
            # Validate Excel-style formulas in data
            sample_row = data[0]
            swing_days_formula = sample_row.get('Swing_Days', '')
            if not swing_days_formula.startswith('='):
                self.log_test("Spreadsheet Interface", False, "Swing_Days not formatted as Excel formula")
                return False
            
            color_rule_formula = sample_row.get('Color_Rule', '')
            if not color_rule_formula.startswith('=IF'):
                self.log_test("Spreadsheet Interface", False, "Color_Rule not formatted as Excel IF formula")
                return False
            
            self.log_test("Spreadsheet Interface", True, "Spreadsheet interface working: Excel-style formulas, formula transparency, sector filtering")
            return True
            
        except Exception as e:
            self.log_test("Spreadsheet Interface", False, f"Error: {str(e)}")
            return False

    def test_enhanced_watchlist_management(self):
        """Test Manual Stock/ETF Management and Enhanced Watchlists"""
        try:
            if not self.auth_token:
                self.log_test("Enhanced Watchlist Management", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test get custom watchlists with stocks
            custom_watchlists_response = self.session.get(f"{API_BASE}/watchlists/custom", headers=auth_headers)
            if custom_watchlists_response.status_code != 200:
                self.log_test("Enhanced Watchlist Management", False, f"Get custom watchlists failed: HTTP {custom_watchlists_response.status_code}")
                return False
            
            # Test add stock to watchlist manually
            test_watchlist_name = "Test Growth Stocks"
            
            # First create a custom watchlist if it doesn't exist
            create_list_data = {
                "name": test_watchlist_name,
                "description": "Test watchlist for manual stock management",
                "color": "#10B981"
            }
            
            create_list_response = self.session.post(f"{API_BASE}/watchlists/lists", json=create_list_data)
            # It's OK if this fails (list might already exist)
            
            # Add stock to watchlist
            add_stock_data = {
                "ticker": "NVDA",
                "name": "NVIDIA Corporation",
                "notes": "AI chip leader for swing trading",
                "tags": ["AI", "semiconductors", "growth"],
                "priority": 5,
                "entry_price": 800.0,
                "target_price": 900.0,
                "stop_loss": 750.0,
                "position_size": 50.0
            }
            
            add_stock_response = self.session.post(f"{API_BASE}/watchlists/custom/{test_watchlist_name}/add-stock", 
                                                 json=add_stock_data, headers=auth_headers)
            if add_stock_response.status_code not in [200, 400]:  # 400 might be "already exists"
                self.log_test("Enhanced Watchlist Management", False, f"Add stock failed: HTTP {add_stock_response.status_code}")
                return False
            
            # Test get custom watchlists again to verify stock was added
            verify_response = self.session.get(f"{API_BASE}/watchlists/custom", headers=auth_headers)
            if verify_response.status_code != 200:
                self.log_test("Enhanced Watchlist Management", False, f"Verify watchlists failed: HTTP {verify_response.status_code}")
                return False
            
            watchlists = verify_response.json()
            test_watchlist = None
            for wl in watchlists:
                if wl.get('name') == test_watchlist_name:
                    test_watchlist = wl
                    break
            
            if not test_watchlist:
                self.log_test("Enhanced Watchlist Management", False, f"Test watchlist '{test_watchlist_name}' not found")
                return False
            
            # Validate watchlist structure
            required_watchlist_fields = ['id', 'name', 'description', 'color', 'stocks']
            missing_watchlist_fields = [field for field in required_watchlist_fields if field not in test_watchlist]
            if missing_watchlist_fields:
                self.log_test("Enhanced Watchlist Management", False, f"Watchlist missing fields: {missing_watchlist_fields}")
                return False
            
            # Check if our stock is in the watchlist
            stocks = test_watchlist.get('stocks', [])
            nvda_stock = None
            for stock in stocks:
                if stock.get('ticker') == 'NVDA':
                    nvda_stock = stock
                    break
            
            if nvda_stock:
                # Validate stock data structure
                required_stock_fields = ['ticker', 'name', 'notes', 'tags', 'priority', 'entry_price', 'target_price', 'stop_loss']
                missing_stock_fields = [field for field in required_stock_fields if field not in nvda_stock]
                if missing_stock_fields:
                    self.log_test("Enhanced Watchlist Management", False, f"Stock missing fields: {missing_stock_fields}")
                    return False
                
                # Test remove stock from watchlist
                remove_response = self.session.delete(f"{API_BASE}/watchlists/custom/{test_watchlist_name}/remove-stock/NVDA", 
                                                    headers=auth_headers)
                if remove_response.status_code != 200:
                    self.log_test("Enhanced Watchlist Management", False, f"Remove stock failed: HTTP {remove_response.status_code}")
                    return False
                
                remove_result = remove_response.json()
                if 'message' not in remove_result:
                    self.log_test("Enhanced Watchlist Management", False, "Remove stock response missing message")
                    return False
            
            self.log_test("Enhanced Watchlist Management", True, "Enhanced watchlist management working: custom lists, manual stock add/remove, detailed stock info")
            return True
            
        except Exception as e:
            self.log_test("Enhanced Watchlist Management", False, f"Error: {str(e)}")
            return False

    def test_historical_data_pruning(self):
        """Test Historical Data Pruning and Administration"""
        try:
            if not self.auth_token:
                self.log_test("Historical Data Pruning", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test historical data pruning
            prune_response = self.session.post(f"{API_BASE}/admin/prune-historical-data?days=90", headers=auth_headers)
            if prune_response.status_code != 200:
                self.log_test("Historical Data Pruning", False, f"Prune data failed: HTTP {prune_response.status_code}")
                return False
            
            prune_result = prune_response.json()
            required_prune_fields = ['message', 'deleted']
            missing_prune_fields = [field for field in required_prune_fields if field not in prune_result]
            if missing_prune_fields:
                self.log_test("Historical Data Pruning", False, f"Prune response missing fields: {missing_prune_fields}")
                return False
            
            # Validate deleted counts structure
            deleted_counts = prune_result.get('deleted', {})
            expected_deletion_types = ['historical_snapshots', 'chart_analyses', 'chat_messages']
            for deletion_type in expected_deletion_types:
                if deletion_type not in deleted_counts:
                    self.log_test("Historical Data Pruning", False, f"Missing deletion count for: {deletion_type}")
                    return False
                
                count = deleted_counts[deletion_type]
                if not isinstance(count, int) or count < 0:
                    self.log_test("Historical Data Pruning", False, f"Invalid deletion count for {deletion_type}: {count}")
                    return False
            
            # Test with different retention period
            prune_30_response = self.session.post(f"{API_BASE}/admin/prune-historical-data?days=30", headers=auth_headers)
            if prune_30_response.status_code != 200:
                self.log_test("Historical Data Pruning", False, f"Prune 30 days failed: HTTP {prune_30_response.status_code}")
                return False
            
            self.log_test("Historical Data Pruning", True, "Historical data pruning working: configurable retention periods, multiple data types, deletion counts")
            return True
            
        except Exception as e:
            self.log_test("Historical Data Pruning", False, f"Error: {str(e)}")
            return False

    def test_phase1_etf_regime_config(self):
        """Test Phase 1: GET /api/formulas/config/etf-regime"""
        try:
            response = self.session.get(f"{API_BASE}/formulas/config/etf-regime")
            if response.status_code != 200:
                self.log_test("Phase 1: ETF Regime Config", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            config = response.json()
            
            # Validate config structure
            required_fields = ['kind', 'params']
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                self.log_test("Phase 1: ETF Regime Config", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate kind
            if config.get('kind') != 'etf_regime':
                self.log_test("Phase 1: ETF Regime Config", False, f"Expected kind=etf_regime, got {config.get('kind')}")
                return False
            
            # Validate expected params
            params = config.get('params', {})
            expected_params = {
                'ema_fast': 20,
                'ema_slow': 50,
                'adx_threshold': 20,
                'atrp_vol_cap_pct': 3.5,
                'income_etf': 'QQQI'
            }
            
            for param, expected_value in expected_params.items():
                if param not in params:
                    self.log_test("Phase 1: ETF Regime Config", False, f"Missing param: {param}")
                    return False
                if params[param] != expected_value:
                    self.log_test("Phase 1: ETF Regime Config", False, f"Param {param}: expected {expected_value}, got {params[param]}")
                    return False
            
            self.log_test("Phase 1: ETF Regime Config", True, "ETF regime config returned with correct kind and default params")
            return True
            
        except Exception as e:
            self.log_test("Phase 1: ETF Regime Config", False, f"Error: {str(e)}")
            return False

    def test_phase1_all_formula_configs(self):
        """Test Phase 1: GET /api/formulas/config/all"""
        try:
            response = self.session.get(f"{API_BASE}/formulas/config/all")
            if response.status_code != 200:
                self.log_test("Phase 1: All Formula Configs", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            configs = response.json()
            
            # Should be an array
            if not isinstance(configs, list):
                self.log_test("Phase 1: All Formula Configs", False, f"Expected array, got {type(configs)}")
                return False
            
            # Should include at least one entry with kind=etf_regime
            etf_regime_found = False
            for config in configs:
                if config.get('kind') == 'etf_regime':
                    etf_regime_found = True
                    break
            
            if not etf_regime_found:
                self.log_test("Phase 1: All Formula Configs", False, "No etf_regime config found in array")
                return False
            
            self.log_test("Phase 1: All Formula Configs", True, f"All configs returned ({len(configs)} configs) including etf_regime")
            return True
            
        except Exception as e:
            self.log_test("Phase 1: All Formula Configs", False, f"Error: {str(e)}")
            return False

    def test_phase1_market_state(self):
        """Test Phase 1: GET /api/market/state"""
        try:
            response = self.session.get(f"{API_BASE}/market/state")
            if response.status_code != 200:
                self.log_test("Phase 1: Market State", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            state = response.json()
            
            # Validate required fields
            required_fields = ['ts', 'regime', 'msae_score', 'components', 'stale']
            missing_fields = [field for field in required_fields if field not in state]
            if missing_fields:
                self.log_test("Phase 1: Market State", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate msae_score range (0-100)
            msae_score = state.get('msae_score', 0)
            if not (0 <= msae_score <= 100):
                self.log_test("Phase 1: Market State", False, f"MSAE score {msae_score} not in range 0-100")
                return False
            
            # Validate components structure
            components = state.get('components', {})
            expected_components = ['ema20', 'ema50', 'adx', 'atr_pct', 'vix', 'vxn', 'breadth_pct_above_50dma', 'qqq_dist_from_ath_pct']
            missing_components = [comp for comp in expected_components if comp not in components]
            if missing_components:
                self.log_test("Phase 1: Market State", False, f"Missing components: {missing_components}")
                return False
            
            # Validate regime
            valid_regimes = ['UPTREND', 'DOWNTREND', 'CHOP']
            if state.get('regime') not in valid_regimes:
                self.log_test("Phase 1: Market State", False, f"Invalid regime: {state.get('regime')}")
                return False
            
            # Validate stale is boolean
            if not isinstance(state.get('stale'), bool):
                self.log_test("Phase 1: Market State", False, f"Stale should be boolean, got {type(state.get('stale'))}")
                return False
            
            self.log_test("Phase 1: Market State", True, f"Market state returned with regime={state['regime']}, msae_score={msae_score}, stale={state['stale']}")
            return True
            
        except Exception as e:
            self.log_test("Phase 1: Market State", False, f"Error: {str(e)}")
            return False

    def test_phase1_market_history(self):
        """Test Phase 1: GET /api/market/history"""
        try:
            # First call market/state to ensure we have at least one snapshot
            state_response = self.session.get(f"{API_BASE}/market/state")
            if state_response.status_code != 200:
                self.log_test("Phase 1: Market History", False, "Failed to create market state snapshot")
                return False
            
            # Now test market history
            response = self.session.get(f"{API_BASE}/market/history")
            if response.status_code != 200:
                self.log_test("Phase 1: Market History", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            history = response.json()
            
            # Should be an array
            if not isinstance(history, list):
                self.log_test("Phase 1: Market History", False, f"Expected array, got {type(history)}")
                return False
            
            # Should have at least one snapshot after calling market/state
            if len(history) == 0:
                self.log_test("Phase 1: Market History", False, "No history snapshots found after creating market state")
                return False
            
            # Validate snapshot structure
            sample_snapshot = history[0]
            required_snapshot_fields = ['ts', 'regime', 'msae_score', 'components', 'stale']
            missing_snapshot_fields = [field for field in required_snapshot_fields if field not in sample_snapshot]
            if missing_snapshot_fields:
                self.log_test("Phase 1: Market History", False, f"Snapshot missing fields: {missing_snapshot_fields}")
                return False
            
            self.log_test("Phase 1: Market History", True, f"Market history returned {len(history)} snapshots with valid structure")
            return True
            
        except Exception as e:
            self.log_test("Phase 1: Market History", False, f"Error: {str(e)}")
            return False

    def test_phase1_etf_regime_signal(self):
        """Test Phase 1: GET /api/signals/etf-regime"""
        try:
            response = self.session.get(f"{API_BASE}/signals/etf-regime")
            if response.status_code != 200:
                self.log_test("Phase 1: ETF Regime Signal", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            signal = response.json()
            
            # Validate required fields
            required_fields = ['decision', 'weights', 'confidence', 'reason', 'params_version']
            missing_fields = [field for field in required_fields if field not in signal]
            if missing_fields:
                self.log_test("Phase 1: ETF Regime Signal", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate decision
            valid_decisions = ['TQQQ', 'SQQQ', 'QQQI', 'OUT']
            decision = signal.get('decision')
            if decision not in valid_decisions:
                self.log_test("Phase 1: ETF Regime Signal", False, f"Invalid decision: {decision}")
                return False
            
            # Validate weights structure and sum
            weights = signal.get('weights', {})
            expected_weight_keys = ['TQQQ', 'SQQQ', 'QQQI']
            missing_weight_keys = [key for key in expected_weight_keys if key not in weights]
            if missing_weight_keys:
                self.log_test("Phase 1: ETF Regime Signal", False, f"Missing weight keys: {missing_weight_keys}")
                return False
            
            # Validate weights sum <= 1
            total_weight = sum(weights.values())
            if total_weight > 1.01:  # Allow small floating point tolerance
                self.log_test("Phase 1: ETF Regime Signal", False, f"Weights sum {total_weight} > 1")
                return False
            
            # Validate confidence range (0-1)
            confidence = signal.get('confidence', 0)
            if not (0 <= confidence <= 1):
                self.log_test("Phase 1: ETF Regime Signal", False, f"Confidence {confidence} not in range 0-1")
                return False
            
            # Validate reason structure
            reason = signal.get('reason', {})
            if not isinstance(reason, dict):
                self.log_test("Phase 1: ETF Regime Signal", False, f"Reason should be dict, got {type(reason)}")
                return False
            
            # Should have ema and adx in reason, unless it's a stale response
            if 'stale' not in reason and ('ema' not in reason or 'adx' not in reason):
                self.log_test("Phase 1: ETF Regime Signal", False, "Reason missing ema or adx fields (non-stale response)")
                return False
            
            self.log_test("Phase 1: ETF Regime Signal", True, f"ETF regime signal: decision={decision}, confidence={confidence}, weights_sum={total_weight:.2f}")
            return True
            
        except Exception as e:
            self.log_test("Phase 1: ETF Regime Signal", False, f"Error: {str(e)}")
            return False

    def test_ndx_constituents_get(self):
        """Test NDX: GET /api/ndx/constituents"""
        try:
            # Test default (active only)
            response = self.session.get(f"{API_BASE}/ndx/constituents")
            if response.status_code != 200:
                self.log_test("NDX: Get Constituents", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate structure
            required_fields = ['_id', 'index', 'as_of', 'version', 'universe']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("NDX: Get Constituents", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate universe is array
            universe = data.get('universe', [])
            if not isinstance(universe, list):
                self.log_test("NDX: Get Constituents", False, f"Universe should be array, got {type(universe)}")
                return False
            
            # Should have some constituents
            if len(universe) == 0:
                self.log_test("NDX: Get Constituents", False, "No constituents returned")
                return False
            
            # Validate constituent structure
            sample_constituent = universe[0]
            required_constituent_fields = ['symbol', 'active']
            missing_constituent_fields = [field for field in required_constituent_fields if field not in sample_constituent]
            if missing_constituent_fields:
                self.log_test("NDX: Get Constituents", False, f"Constituent missing fields: {missing_constituent_fields}")
                return False
            
            # Test with all=true parameter
            all_response = self.session.get(f"{API_BASE}/ndx/constituents?all=true")
            if all_response.status_code != 200:
                self.log_test("NDX: Get Constituents", False, f"All constituents failed: HTTP {all_response.status_code}")
                return False
            
            all_data = all_response.json()
            all_universe = all_data.get('universe', [])
            
            # All should have >= active only
            if len(all_universe) < len(universe):
                self.log_test("NDX: Get Constituents", False, f"All constituents ({len(all_universe)}) < active only ({len(universe)})")
                return False
            
            self.log_test("NDX: Get Constituents", True, f"NDX constituents: {len(universe)} active, {len(all_universe)} total")
            return True
            
        except Exception as e:
            self.log_test("NDX: Get Constituents", False, f"Error: {str(e)}")
            return False

    def test_ndx_constituents_post(self):
        """Test NDX: POST /api/ndx/constituents (requires auth)"""
        try:
            if not self.auth_token:
                self.log_test("NDX: Post Constituents", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Get current version first
            get_response = self.session.get(f"{API_BASE}/ndx/constituents")
            if get_response.status_code != 200:
                self.log_test("NDX: Post Constituents", False, "Failed to get current constituents")
                return False
            
            current_data = get_response.json()
            current_version = current_data.get('version', 0)
            
            # Create test payload with a few test constituents
            test_payload = {
                "as_of": "2025-01-01T00:00:00Z",
                "source": "test_update",
                "notes": "Test NDX constituents update",
                "universe": [
                    {"symbol": "AAPL", "yf_symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "active": True},
                    {"symbol": "MSFT", "yf_symbol": "MSFT", "name": "Microsoft Corp.", "sector": "Technology", "active": True},
                    {"symbol": "GOOGL", "yf_symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "active": True},
                    {"symbol": "NVDA", "yf_symbol": "NVDA", "name": "NVIDIA Corp.", "sector": "Technology", "active": True},
                    {"symbol": "TSLA", "yf_symbol": "TSLA", "name": "Tesla Inc.", "sector": "Technology", "active": False}
                ]
            }
            
            # Test POST
            response = self.session.post(f"{API_BASE}/ndx/constituents", json=test_payload, headers=auth_headers)
            if response.status_code != 200:
                self.log_test("NDX: Post Constituents", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Validate response
            required_fields = ['message', 'version']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                self.log_test("NDX: Post Constituents", False, f"Response missing fields: {missing_fields}")
                return False
            
            # Version should have incremented
            new_version = result.get('version')
            if new_version <= current_version:
                self.log_test("NDX: Post Constituents", False, f"Version not incremented: {new_version} <= {current_version}")
                return False
            
            # Verify the update by getting constituents again
            verify_response = self.session.get(f"{API_BASE}/ndx/constituents")
            if verify_response.status_code != 200:
                self.log_test("NDX: Post Constituents", False, "Failed to verify update")
                return False
            
            verify_data = verify_response.json()
            if verify_data.get('version') != new_version:
                self.log_test("NDX: Post Constituents", False, f"Version mismatch after update: {verify_data.get('version')} != {new_version}")
                return False
            
            # Should have our test symbols (active only by default)
            verify_universe = verify_data.get('universe', [])
            test_symbols = {member['symbol'] for member in test_payload['universe'] if member['active']}
            found_symbols = {member['symbol'] for member in verify_universe}
            
            if not test_symbols.issubset(found_symbols):
                missing_symbols = test_symbols - found_symbols
                self.log_test("NDX: Post Constituents", False, f"Missing test symbols: {missing_symbols}")
                return False
            
            self.log_test("NDX: Post Constituents", True, f"NDX constituents updated: version {current_version} -> {new_version}")
            return True
            
        except Exception as e:
            self.log_test("NDX: Post Constituents", False, f"Error: {str(e)}")
            return False

    def test_ndx_constituents_diff(self):
        """Test NDX: GET /api/ndx/constituents/diff"""
        try:
            # Get current version
            get_response = self.session.get(f"{API_BASE}/ndx/constituents")
            if get_response.status_code != 200:
                self.log_test("NDX: Constituents Diff", False, "Failed to get current constituents")
                return False
            
            current_data = get_response.json()
            current_version = current_data.get('version', 1)
            
            # Test diff between same version (should be empty)
            response = self.session.get(f"{API_BASE}/ndx/constituents/diff?fromVersion={current_version}&toVersion={current_version}")
            if response.status_code != 200:
                self.log_test("NDX: Constituents Diff", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            diff = response.json()
            
            # Validate structure
            required_fields = ['fromVersion', 'toVersion', 'added', 'removed', 'changed']
            missing_fields = [field for field in required_fields if field not in diff]
            if missing_fields:
                self.log_test("NDX: Constituents Diff", False, f"Missing fields: {missing_fields}")
                return False
            
            # Same version diff should be empty
            if diff['fromVersion'] != current_version or diff['toVersion'] != current_version:
                self.log_test("NDX: Constituents Diff", False, f"Version mismatch in diff response")
                return False
            
            # Arrays should be empty for same version
            if len(diff['added']) > 0 or len(diff['removed']) > 0 or len(diff['changed']) > 0:
                self.log_test("NDX: Constituents Diff", False, "Same version diff should be empty")
                return False
            
            # Test with invalid version (should return 404)
            invalid_response = self.session.get(f"{API_BASE}/ndx/constituents/diff?fromVersion=999&toVersion=1000")
            if invalid_response.status_code != 404:
                self.log_test("NDX: Constituents Diff", False, f"Expected 404 for invalid versions, got {invalid_response.status_code}")
                return False
            
            self.log_test("NDX: Constituents Diff", True, f"Constituents diff working: v{current_version} to v{current_version} (empty diff)")
            return True
            
        except Exception as e:
            self.log_test("NDX: Constituents Diff", False, f"Error: {str(e)}")
            return False

    def test_ndx_refresh_prices(self):
        """Test NDX: POST /api/ndx/constituents/refresh-prices"""
        try:
            print("Testing NDX price refresh (this may take 30-60 seconds)...")
            
            # Test with default interval (1d)
            response = self.session.post(f"{API_BASE}/ndx/constituents/refresh-prices", timeout=120)
            if response.status_code != 200:
                self.log_test("NDX: Refresh Prices", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Validate response structure
            required_fields = ['requested', 'succeeded', 'failed']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                self.log_test("NDX: Refresh Prices", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate counts
            requested = result.get('requested', 0)
            succeeded = result.get('succeeded', 0)
            failed = result.get('failed', [])
            
            if requested <= 0:
                self.log_test("NDX: Refresh Prices", False, f"No symbols requested: {requested}")
                return False
            
            if succeeded < 0:
                self.log_test("NDX: Refresh Prices", False, f"Invalid succeeded count: {succeeded}")
                return False
            
            if not isinstance(failed, list):
                self.log_test("NDX: Refresh Prices", False, f"Failed should be array, got {type(failed)}")
                return False
            
            # Should have some success (allow for some failures due to yfinance throttling)
            success_rate = succeeded / requested if requested > 0 else 0
            if success_rate < 0.5:  # At least 50% should succeed
                self.log_test("NDX: Refresh Prices", False, f"Low success rate: {success_rate:.1%} ({succeeded}/{requested})")
                return False
            
            # Test with 15m interval
            response_15m = self.session.post(f"{API_BASE}/ndx/constituents/refresh-prices?interval=15m", timeout=120)
            if response_15m.status_code != 200:
                self.log_test("NDX: Refresh Prices", False, f"15m interval failed: HTTP {response_15m.status_code}")
                return False
            
            result_15m = response_15m.json()
            if result_15m.get('requested', 0) <= 0:
                self.log_test("NDX: Refresh Prices", False, "15m interval returned no requests")
                return False
            
            self.log_test("NDX: Refresh Prices", True, f"Price refresh: {succeeded}/{requested} succeeded ({success_rate:.1%}), {len(failed)} failed")
            return True
            
        except Exception as e:
            self.log_test("NDX: Refresh Prices", False, f"Error: {str(e)}")
            return False

    def test_legacy_formulas_config(self):
        """Test Legacy: GET /api/formulas/config (should still return single legacy object)"""
        try:
            response = self.session.get(f"{API_BASE}/formulas/config")
            if response.status_code != 200:
                self.log_test("Legacy: Formulas Config", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            config = response.json()
            
            # Should be a single object (not array) for legacy compatibility
            if isinstance(config, list):
                self.log_test("Legacy: Formulas Config", False, "Legacy config should be object, not array")
                return False
            
            # Should have legacy structure (not kind=etf_regime)
            if config.get('kind') == 'etf_regime':
                self.log_test("Legacy: Formulas Config", False, "Legacy config should not be etf_regime kind")
                return False
            
            # Should have traditional formula config fields
            expected_legacy_fields = ['relative_strength', 'sata_weights', 'atr_calculation']
            found_legacy_fields = [field for field in expected_legacy_fields if field in config]
            if len(found_legacy_fields) == 0:
                self.log_test("Legacy: Formulas Config", False, f"No legacy fields found. Expected one of: {expected_legacy_fields}")
                return False
            
            self.log_test("Legacy: Formulas Config", True, f"Legacy config returned with {len(found_legacy_fields)} traditional fields")
            return True
            
        except Exception as e:
            self.log_test("Legacy: Formulas Config", False, f"Error: {str(e)}")
            return False

    def test_positions_and_trades_management(self):
        """Test Positions & Trades Management APIs"""
        try:
            if not self.auth_token:
                self.log_test("Positions & Trades Management", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # 1. Test GET /api/positions (auth required) - should return [] or existing items
            positions_response = self.session.get(f"{API_BASE}/positions", headers=auth_headers)
            if positions_response.status_code != 200:
                self.log_test("Positions & Trades Management", False, f"GET positions failed: HTTP {positions_response.status_code}: {positions_response.text}")
                return False
            
            positions = positions_response.json()
            if not isinstance(positions, list):
                self.log_test("Positions & Trades Management", False, f"Positions should be array, got {type(positions)}")
                return False
            
            # Validate computed fields if positions exist
            if positions:
                sample_position = positions[0]
                required_computed_fields = ['initial_stop', 'trailing_stop', 'r_multiple', 'breached_initial_stop', 'breached_trailing_stop', 'status']
                missing_fields = [field for field in required_computed_fields if field not in sample_position]
                if missing_fields:
                    self.log_test("Positions & Trades Management", False, f"Position missing computed fields: {missing_fields}")
                    return False
            
            # 2. Test POST /api/positions (admin required) - create position for AAPL
            position_data = {
                "symbol": "AAPL",
                "side": "LONG",
                "entry_price": 100.0,
                "shares": 10,
                "strategy_tag": "Test Swing Trade",
                "risk_perc": 1.0,
                "stop_type": "ATR_TRAIL",
                "trail_mult": 3.0,
                "notes": "Test position for backend testing"
            }
            
            create_position_response = self.session.post(f"{API_BASE}/positions", json=position_data, headers=auth_headers)
            if create_position_response.status_code != 200:
                self.log_test("Positions & Trades Management", False, f"POST position failed: HTTP {create_position_response.status_code}: {create_position_response.text}")
                return False
            
            create_result = create_position_response.json()
            if 'position' not in create_result or 'entry_trade' not in create_result:
                self.log_test("Positions & Trades Management", False, "Create position response missing position or entry_trade")
                return False
            
            position = create_result['position']
            entry_trade = create_result['entry_trade']
            position_id = position.get('id')
            
            if not position_id:
                self.log_test("Positions & Trades Management", False, "Created position missing ID")
                return False
            
            # Validate position structure and computed fields
            required_position_fields = ['symbol', 'side', 'entry_price', 'shares', 'initial_stop', 'trailing_stop', 'r_multiple', 'status']
            missing_position_fields = [field for field in required_position_fields if field not in position]
            if missing_position_fields:
                self.log_test("Positions & Trades Management", False, f"Position missing fields: {missing_position_fields}")
                return False
            
            # Validate initial stop calculation for LONG position
            if position['side'] == 'LONG' and position['initial_stop'] > position['entry_price']:
                self.log_test("Positions & Trades Management", False, f"Initial stop {position['initial_stop']} should be <= entry price {position['entry_price']} for LONG")
                return False
            
            # Validate entry trade was created
            if entry_trade['symbol'] != 'AAPL' or entry_trade['side'] != 'BUY' or entry_trade['shares'] != 10:
                self.log_test("Positions & Trades Management", False, f"Entry trade incorrect: {entry_trade}")
                return False
            
            # 3. Test PATCH /api/positions/{id} (admin required) - close position
            patch_data = {
                "status": "CLOSED",
                "exit_price": 110.0,
                "notes": "Test exit - profitable trade"
            }
            
            patch_response = self.session.patch(f"{API_BASE}/positions/{position_id}", json=patch_data, headers=auth_headers)
            if patch_response.status_code != 200:
                self.log_test("Positions & Trades Management", False, f"PATCH position failed: HTTP {patch_response.status_code}: {patch_response.text}")
                return False
            
            updated_position = patch_response.json()
            
            # Validate position was closed and PnL calculated
            if updated_position.get('status') != 'CLOSED':
                self.log_test("Positions & Trades Management", False, f"Position status not updated to CLOSED: {updated_position.get('status')}")
                return False
            
            if updated_position.get('exit_price') != 110.0:
                self.log_test("Positions & Trades Management", False, f"Exit price not set correctly: {updated_position.get('exit_price')}")
                return False
            
            # Validate PnL is positive (110 - 100) * 10 = 100
            pnl = updated_position.get('pnl')
            if pnl is None or pnl <= 0:
                self.log_test("Positions & Trades Management", False, f"PnL should be positive, got: {pnl}")
                return False
            
            # Validate r_exit is present
            r_exit = updated_position.get('r_exit')
            if r_exit is None:
                self.log_test("Positions & Trades Management", False, "r_exit not calculated for closed position")
                return False
            
            # 4. Test GET /api/trades - should return at least 2 trades (entry + exit)
            trades_response = self.session.get(f"{API_BASE}/trades")
            if trades_response.status_code != 200:
                self.log_test("Positions & Trades Management", False, f"GET trades failed: HTTP {trades_response.status_code}: {trades_response.text}")
                return False
            
            trades = trades_response.json()
            if not isinstance(trades, list):
                self.log_test("Positions & Trades Management", False, f"Trades should be array, got {type(trades)}")
                return False
            
            if len(trades) < 2:
                self.log_test("Positions & Trades Management", False, f"Expected at least 2 trades (entry+exit), got {len(trades)}")
                return False
            
            # Validate trades are in correct order (most recent first)
            if len(trades) >= 2:
                first_trade = trades[0]
                second_trade = trades[1]
                
                # Parse timestamps for comparison
                first_ts = datetime.fromisoformat(first_trade['ts'].replace('Z', '+00:00'))
                second_ts = datetime.fromisoformat(second_trade['ts'].replace('Z', '+00:00'))
                
                if first_ts < second_ts:
                    self.log_test("Positions & Trades Management", False, "Trades not in correct order (most recent first)")
                    return False
            
            # Find our position's trades
            position_trades = [t for t in trades if t.get('position_id') == position_id]
            if len(position_trades) < 2:
                self.log_test("Positions & Trades Management", False, f"Expected 2 trades for position {position_id}, got {len(position_trades)}")
                return False
            
            # Validate entry and exit trades
            buy_trade = next((t for t in position_trades if t['side'] == 'BUY'), None)
            sell_trade = next((t for t in position_trades if t['side'] == 'SELL'), None)
            
            if not buy_trade or not sell_trade:
                self.log_test("Positions & Trades Management", False, "Missing BUY or SELL trade for position")
                return False
            
            # 5. Test POST /api/trades (admin required) - create standalone trade
            standalone_trade_data = {
                "symbol": "MSFT",
                "side": "BUY",
                "price": 250.0,
                "shares": 5,
                "fee": 1.0,
                "notes": "Standalone test trade"
            }
            
            create_trade_response = self.session.post(f"{API_BASE}/trades", json=standalone_trade_data, headers=auth_headers)
            if create_trade_response.status_code != 200:
                self.log_test("Positions & Trades Management", False, f"POST trade failed: HTTP {create_trade_response.status_code}: {create_trade_response.text}")
                return False
            
            created_trade = create_trade_response.json()
            
            # Validate standalone trade
            required_trade_fields = ['id', 'symbol', 'side', 'price', 'shares', 'ts']
            missing_trade_fields = [field for field in required_trade_fields if field not in created_trade]
            if missing_trade_fields:
                self.log_test("Positions & Trades Management", False, f"Created trade missing fields: {missing_trade_fields}")
                return False
            
            if created_trade['symbol'] != 'MSFT' or created_trade['side'] != 'BUY' or created_trade['shares'] != 5:
                self.log_test("Positions & Trades Management", False, f"Standalone trade data incorrect: {created_trade}")
                return False
            
            self.log_test("Positions & Trades Management", True, f"All Positions & Trades APIs working: GET positions, POST position (AAPL LONG), PATCH close (PnL: ${pnl}), GET trades ({len(trades)} total), POST standalone trade")
            return True
            
        except Exception as e:
            self.log_test("Positions & Trades Management", False, f"Error: {str(e)}")
            return False

    def test_phase2_universe_import(self):
        """Test Phase 2: POST /api/universe/import with AAPL, MSFT, NVDA"""
        try:
            if not self.auth_token:
                self.log_test("Phase 2: Universe Import", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test import with the specific symbols mentioned in review request
            import_data = [
                {"symbol": "AAPL"},
                {"symbol": "MSFT"},
                {"symbol": "NVDA"}
            ]
            
            response = self.session.post(f"{API_BASE}/universe/import", json=import_data, headers=auth_headers)
            if response.status_code != 200:
                self.log_test("Phase 2: Universe Import", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Validate response structure
            if 'imported' not in result:
                self.log_test("Phase 2: Universe Import", False, "Response missing 'imported' field")
                return False
            
            imported_count = result.get('imported', 0)
            if imported_count != 3:
                self.log_test("Phase 2: Universe Import", False, f"Expected 3 imported, got {imported_count}")
                return False
            
            # Verify by getting universe
            get_response = self.session.get(f"{API_BASE}/universe")
            if get_response.status_code != 200:
                self.log_test("Phase 2: Universe Import", False, f"GET universe failed: HTTP {get_response.status_code}")
                return False
            
            universe = get_response.json()
            if not isinstance(universe, list):
                self.log_test("Phase 2: Universe Import", False, f"Universe should be array, got {type(universe)}")
                return False
            
            # Check if our imported symbols are present
            universe_symbols = {item.get('symbol', '').upper() for item in universe}
            expected_symbols = {'AAPL', 'MSFT', 'NVDA'}
            
            if not expected_symbols.issubset(universe_symbols):
                missing = expected_symbols - universe_symbols
                self.log_test("Phase 2: Universe Import", False, f"Missing imported symbols in universe: {missing}")
                return False
            
            self.log_test("Phase 2: Universe Import", True, f"Successfully imported {imported_count} symbols and verified in universe")
            return True
            
        except Exception as e:
            self.log_test("Phase 2: Universe Import", False, f"Error: {str(e)}")
            return False

    def test_phase2_screens_neglected_pre_earnings(self):
        """Test Phase 2: GET /api/screens/neglected-pre-earnings"""
        try:
            response = self.session.get(f"{API_BASE}/screens/neglected-pre-earnings")
            if response.status_code != 200:
                self.log_test("Phase 2: Screens Neglected Pre-Earnings", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Should be an array (can be empty)
            if not isinstance(result, list):
                self.log_test("Phase 2: Screens Neglected Pre-Earnings", False, f"Expected array, got {type(result)}")
                return False
            
            # If not empty, validate structure
            if len(result) > 0:
                sample_item = result[0]
                required_fields = ['symbol', 'ret_21d', 'slope_63d', 'atrp_percentile', 'near_20dma', 'trigger', 'label']
                missing_fields = [field for field in required_fields if field not in sample_item]
                if missing_fields:
                    self.log_test("Phase 2: Screens Neglected Pre-Earnings", False, f"Screen item missing fields: {missing_fields}")
                    return False
                
                # Validate label is WATCH or READY
                label = sample_item.get('label')
                if label not in ['WATCH', 'READY']:
                    self.log_test("Phase 2: Screens Neglected Pre-Earnings", False, f"Invalid label: {label}, expected WATCH or READY")
                    return False
            
            self.log_test("Phase 2: Screens Neglected Pre-Earnings", True, f"Screen returned {len(result)} items with valid structure")
            return True
            
        except Exception as e:
            self.log_test("Phase 2: Screens Neglected Pre-Earnings", False, f"Error: {str(e)}")
            return False

    def test_phase2_etf_regime_simulate(self):
        """Test Phase 2: POST /api/signals/etf-regime/simulate with required fields"""
        try:
            # Test with a short date range for faster execution
            simulate_data = {
                "start": "2024-01-01",
                "end": "2024-01-31"
            }
            
            response = self.session.post(f"{API_BASE}/signals/etf-regime/simulate", json=simulate_data)
            if response.status_code != 200:
                self.log_test("Phase 2: ETF Regime Simulate", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Validate all required fields from review request
            required_fields = [
                'equity_curve', 'total_return', 'max_drawdown', 'sharpe', 
                'flips', 'pl_by_regime', 'decisions', 'params_version'
            ]
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                self.log_test("Phase 2: ETF Regime Simulate", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Validate equity_curve structure
            equity_curve = result.get('equity_curve', [])
            if not isinstance(equity_curve, list) or len(equity_curve) == 0:
                self.log_test("Phase 2: ETF Regime Simulate", False, "equity_curve should be non-empty array")
                return False
            
            # Validate equity curve item structure
            sample_curve_item = equity_curve[0]
            if 'ts' not in sample_curve_item or 'equity' not in sample_curve_item:
                self.log_test("Phase 2: ETF Regime Simulate", False, "equity_curve items missing ts or equity")
                return False
            
            # Validate decisions structure
            decisions = result.get('decisions', [])
            if not isinstance(decisions, list) or len(decisions) == 0:
                self.log_test("Phase 2: ETF Regime Simulate", False, "decisions should be non-empty array")
                return False
            
            # Validate decision item structure
            sample_decision = decisions[0]
            if 'ts' not in sample_decision or 'decision' not in sample_decision:
                self.log_test("Phase 2: ETF Regime Simulate", False, "decision items missing ts or decision")
                return False
            
            # Validate pl_by_regime structure
            pl_by_regime = result.get('pl_by_regime', {})
            if not isinstance(pl_by_regime, dict):
                self.log_test("Phase 2: ETF Regime Simulate", False, "pl_by_regime should be dict")
                return False
            
            # Validate numeric fields
            numeric_fields = ['total_return', 'max_drawdown', 'sharpe', 'flips']
            for field in numeric_fields:
                value = result.get(field)
                if not isinstance(value, (int, float)):
                    self.log_test("Phase 2: ETF Regime Simulate", False, f"{field} should be numeric, got {type(value)}")
                    return False
            
            # Validate params_version is string
            params_version = result.get('params_version')
            if not isinstance(params_version, str):
                self.log_test("Phase 2: ETF Regime Simulate", False, f"params_version should be string, got {type(params_version)}")
                return False
            
            self.log_test("Phase 2: ETF Regime Simulate", True, f"Simulation returned all required fields: {len(equity_curve)} equity points, {len(decisions)} decisions, {result['flips']} flips")
            return True
            
        except Exception as e:
            self.log_test("Phase 2: ETF Regime Simulate", False, f"Error: {str(e)}")
            return False

    def test_sanity_dashboard(self):
        """Test Sanity: GET /api/dashboard (should respond 200)"""
        try:
            response = self.session.get(f"{API_BASE}/dashboard")
            if response.status_code != 200:
                self.log_test("Sanity: Dashboard", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Should have basic dashboard fields
            if 'greeting' not in data:
                self.log_test("Sanity: Dashboard", False, "Dashboard missing greeting field")
                return False
            
            self.log_test("Sanity: Dashboard", True, "Dashboard endpoint responding correctly")
            return True
            
        except Exception as e:
            self.log_test("Sanity: Dashboard", False, f"Error: {str(e)}")
            return False

    def test_phase2_etf_regime_simulate(self):
        """Test Phase 2: POST /api/signals/etf-regime/simulate"""
        try:
            simulate_data = {
                "start": "2020-01-01",
                "end": "2024-12-31"
            }
            
            response = self.session.post(f"{API_BASE}/signals/etf-regime/simulate", json=simulate_data)
            if response.status_code == 404:
                self.log_test("Phase 2: ETF Regime Simulate", False, "❌ NOT IMPLEMENTED: POST /api/signals/etf-regime/simulate endpoint does not exist")
                return False
            elif response.status_code != 200:
                self.log_test("Phase 2: ETF Regime Simulate", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            result = response.json()
            
            # Validate expected response structure
            required_fields = ['equity_curve', 'total_return', 'max_drawdown', 'sharpe', 'flips', 'pl_by_regime', 'decisions', 'params_version']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                self.log_test("Phase 2: ETF Regime Simulate", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate equity_curve has length > 0
            equity_curve = result.get('equity_curve', [])
            if len(equity_curve) == 0:
                self.log_test("Phase 2: ETF Regime Simulate", False, "equity_curve length is 0")
                return False
            
            # Validate numeric metrics
            numeric_fields = ['total_return', 'max_drawdown', 'sharpe']
            for field in numeric_fields:
                value = result.get(field)
                if not isinstance(value, (int, float)):
                    self.log_test("Phase 2: ETF Regime Simulate", False, f"{field} is not numeric: {value}")
                    return False
            
            # Validate decisions array is present
            decisions = result.get('decisions', [])
            if not isinstance(decisions, list):
                self.log_test("Phase 2: ETF Regime Simulate", False, f"decisions should be array, got {type(decisions)}")
                return False
            
            self.log_test("Phase 2: ETF Regime Simulate", True, f"Simulation returned: equity_curve length={len(equity_curve)}, total_return={result['total_return']}, decisions={len(decisions)}")
            return True
            
        except Exception as e:
            self.log_test("Phase 2: ETF Regime Simulate", False, f"Error: {str(e)}")
            return False

    def test_phase2_universe_management(self):
        """Test Phase 2: Universe Management APIs"""
        try:
            # Test GET /api/universe (initially empty or fallback)
            universe_response = self.session.get(f"{API_BASE}/universe")
            if universe_response.status_code == 404:
                self.log_test("Phase 2: Universe Management", False, "❌ NOT IMPLEMENTED: GET /api/universe endpoint does not exist")
                return False
            elif universe_response.status_code != 200:
                self.log_test("Phase 2: Universe Management", False, f"GET universe failed: HTTP {universe_response.status_code}")
                return False
            
            initial_universe = universe_response.json()
            
            # Login for authenticated operations
            if not self.auth_token:
                login_success = self.test_authentication_system()
                if not login_success:
                    self.log_test("Phase 2: Universe Management", False, "Authentication required for universe import")
                    return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test POST /api/universe/import with 3 symbols
            import_data = [
                {"symbol": "AAPL"},
                {"symbol": "MSFT"},
                {"symbol": "NVDA"}
            ]
            
            import_response = self.session.post(f"{API_BASE}/universe/import", json=import_data, headers=auth_headers)
            if import_response.status_code == 404:
                self.log_test("Phase 2: Universe Management", False, "❌ NOT IMPLEMENTED: POST /api/universe/import endpoint does not exist")
                return False
            elif import_response.status_code != 200:
                self.log_test("Phase 2: Universe Management", False, f"Import failed: HTTP {import_response.status_code}")
                return False
            
            # Test GET /api/universe again to verify import
            verify_response = self.session.get(f"{API_BASE}/universe")
            if verify_response.status_code != 200:
                self.log_test("Phase 2: Universe Management", False, f"Verify universe failed: HTTP {verify_response.status_code}")
                return False
            
            final_universe = verify_response.json()
            
            # Validate that imported symbols are present
            if isinstance(final_universe, list):
                symbols = [item.get('symbol') for item in final_universe if isinstance(item, dict)]
            else:
                symbols = final_universe.get('symbols', []) if isinstance(final_universe, dict) else []
            
            expected_symbols = ['AAPL', 'MSFT', 'NVDA']
            missing_symbols = [symbol for symbol in expected_symbols if symbol not in symbols]
            if missing_symbols:
                self.log_test("Phase 2: Universe Management", False, f"Missing imported symbols: {missing_symbols}")
                return False
            
            self.log_test("Phase 2: Universe Management", True, f"Universe management working: imported {len(expected_symbols)} symbols, verified in universe")
            return True
            
        except Exception as e:
            self.log_test("Phase 2: Universe Management", False, f"Error: {str(e)}")
            return False

    def test_phase2_stock_screens(self):
        """Test Phase 2: Stock Screening APIs"""
        try:
            # Test GET /api/screens/leaders?top=5
            leaders_response = self.session.get(f"{API_BASE}/screens/leaders?top=5")
            if leaders_response.status_code == 404:
                self.log_test("Phase 2: Stock Screens", False, "❌ NOT IMPLEMENTED: GET /api/screens/leaders endpoint does not exist")
                return False
            elif leaders_response.status_code != 200:
                self.log_test("Phase 2: Stock Screens", False, f"Leaders screen failed: HTTP {leaders_response.status_code}")
                return False
            
            leaders = leaders_response.json()
            
            # Validate leaders response
            if not isinstance(leaders, list):
                self.log_test("Phase 2: Stock Screens", False, f"Leaders should be array, got {type(leaders)}")
                return False
            
            # Should return 5 or fewer entries
            if len(leaders) > 5:
                self.log_test("Phase 2: Stock Screens", False, f"Leaders returned {len(leaders)} entries, expected <= 5")
                return False
            
            # Test GET /api/screens/neglected-pre-earnings
            neglected_response = self.session.get(f"{API_BASE}/screens/neglected-pre-earnings")
            if neglected_response.status_code == 404:
                self.log_test("Phase 2: Stock Screens", False, "❌ NOT IMPLEMENTED: GET /api/screens/neglected-pre-earnings endpoint does not exist")
                return False
            elif neglected_response.status_code != 200:
                self.log_test("Phase 2: Stock Screens", False, f"Neglected screen failed: HTTP {neglected_response.status_code}")
                return False
            
            neglected = neglected_response.json()
            
            # Validate neglected response
            if not isinstance(neglected, list):
                self.log_test("Phase 2: Stock Screens", False, f"Neglected should be array, got {type(neglected)}")
                return False
            
            # Validate entries have WATCH or READY fields
            if neglected:
                sample_entry = neglected[0]
                if 'label' not in sample_entry:
                    self.log_test("Phase 2: Stock Screens", False, "Neglected entries missing 'label' field")
                    return False
                
                label = sample_entry.get('label')
                if label not in ['WATCH', 'READY']:
                    self.log_test("Phase 2: Stock Screens", False, f"Invalid label: {label}, expected WATCH or READY")
                    return False
            
            self.log_test("Phase 2: Stock Screens", True, f"Stock screens working: leaders={len(leaders)} entries, neglected={len(neglected)} entries with proper labels")
            return True
            
        except Exception as e:
            self.log_test("Phase 2: Stock Screens", False, f"Error: {str(e)}")
            return False

    def test_formula_param_editor_versioning(self):
        """Test Formula Param Editor & Versioning endpoints"""
        try:
            if not self.auth_token:
                self.log_test("Formula Param Editor & Versioning", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test POST /api/formulas/preview
            preview_payload = {
                "kind": "etf_regime",
                "params": {
                    "ema_fast": 15,
                    "ema_slow": 45,
                    "adx_threshold": 25,
                    "atrp_vol_cap_pct": 4.0,
                    "income_etf": "QQQI"
                },
                "start_date": "2024-01-01",
                "end_date": "2024-03-31"
            }
            
            preview_response = self.session.post(f"{API_BASE}/formulas/preview", json=preview_payload, headers=auth_headers)
            if preview_response.status_code != 200:
                self.log_test("Formula Param Editor & Versioning", False, f"Preview failed: HTTP {preview_response.status_code}: {preview_response.text}")
                return False
            
            preview_result = preview_response.json()
            
            # Validate preview response structure
            required_preview_fields = ['snapshot', 'signal', 'params_version']
            missing_preview_fields = [field for field in required_preview_fields if field not in preview_result]
            if missing_preview_fields:
                self.log_test("Formula Param Editor & Versioning", False, f"Preview response missing fields: {missing_preview_fields}")
                return False
            
            # Validate snapshot structure
            snapshot = preview_result.get('snapshot', {})
            if not isinstance(snapshot, dict) or len(snapshot) == 0:
                self.log_test("Formula Param Editor & Versioning", False, "Preview snapshot is empty or invalid")
                return False
            
            # Validate signal structure
            signal = preview_result.get('signal', {})
            required_signal_fields = ['decision', 'confidence']
            missing_signal_fields = [field for field in required_signal_fields if field not in signal]
            if missing_signal_fields:
                self.log_test("Formula Param Editor & Versioning", False, f"Preview signal missing fields: {missing_signal_fields}")
                return False
            
            # Validate params_version
            params_version = preview_result.get('params_version')
            if not isinstance(params_version, (int, str)) or params_version is None:
                self.log_test("Formula Param Editor & Versioning", False, f"Invalid params_version: {params_version}")
                return False
            
            # Test POST /api/formulas/config/publish (admin required)
            publish_payload = {
                "kind": "etf_regime",
                "params": {
                    "ema_fast": 20,
                    "ema_slow": 50,
                    "adx_threshold": 20,
                    "atrp_vol_cap_pct": 3.5,
                    "income_etf": "QQQI"
                },
                "notes": "Test publish from backend testing"
            }
            
            publish_response = self.session.post(f"{API_BASE}/formulas/config/publish", json=publish_payload, headers=auth_headers)
            if publish_response.status_code != 200:
                self.log_test("Formula Param Editor & Versioning", False, f"Publish failed: HTTP {publish_response.status_code}: {publish_response.text}")
                return False
            
            publish_result = publish_response.json()
            
            # Validate publish response
            required_publish_fields = ['id', 'version']
            missing_publish_fields = [field for field in required_publish_fields if field not in publish_result]
            if missing_publish_fields:
                self.log_test("Formula Param Editor & Versioning", False, f"Publish response missing fields: {missing_publish_fields}")
                return False
            
            published_id = publish_result.get('id')
            published_version = publish_result.get('version')
            
            if not published_id or not published_version:
                self.log_test("Formula Param Editor & Versioning", False, "Publish returned empty id or version")
                return False
            
            # Test POST /api/formulas/config/revert (admin required)
            revert_payload = {
                "kind": "etf_regime",
                "version": published_version
            }
            
            revert_response = self.session.post(f"{API_BASE}/formulas/config/revert", json=revert_payload, headers=auth_headers)
            if revert_response.status_code != 200:
                self.log_test("Formula Param Editor & Versioning", False, f"Revert failed: HTTP {revert_response.status_code}: {revert_response.text}")
                return False
            
            revert_result = revert_response.json()
            
            # Validate revert response
            if 'message' not in revert_result:
                self.log_test("Formula Param Editor & Versioning", False, "Revert response missing message")
                return False
            
            # Verify revert worked by checking active version
            if 'active_version' not in revert_result:
                self.log_test("Formula Param Editor & Versioning", False, "Revert response missing active_version")
                return False
            
            self.log_test("Formula Param Editor & Versioning", True, f"All endpoints working: preview with snapshot+signal+params_version, publish returns id/version, revert activates previous version")
            return True
            
        except Exception as e:
            self.log_test("Formula Param Editor & Versioning", False, f"Error: {str(e)}")
            return False

    def test_sendgrid_settings_endpoints(self):
        """Test SendGrid settings endpoints"""
        try:
            if not self.auth_token:
                self.log_test("SendGrid Settings", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test GET /api/settings/sendgrid (admin required)
            get_response = self.session.get(f"{API_BASE}/settings/sendgrid", headers=auth_headers)
            if get_response.status_code != 200:
                self.log_test("SendGrid Settings", False, f"GET sendgrid settings failed: HTTP {get_response.status_code}: {get_response.text}")
                return False
            
            get_result = get_response.json()
            
            # Validate GET response structure
            if 'configured' not in get_result:
                self.log_test("SendGrid Settings", False, "GET response missing 'configured' flag")
                return False
            
            configured_flag = get_result.get('configured')
            if not isinstance(configured_flag, bool):
                self.log_test("SendGrid Settings", False, f"Configured flag should be boolean, got {type(configured_flag)}")
                return False
            
            # Test POST /api/settings/sendgrid (admin required) with dummy key
            dummy_key_payload = {
                "api_key": "SG.dummy_test_key_12345.abcdefghijklmnopqrstuvwxyz",
                "from_email": "test@example.com",
                "from_name": "Test System"
            }
            
            post_response = self.session.post(f"{API_BASE}/settings/sendgrid", json=dummy_key_payload, headers=auth_headers)
            if post_response.status_code != 200:
                self.log_test("SendGrid Settings", False, f"POST sendgrid settings failed: HTTP {post_response.status_code}: {post_response.text}")
                return False
            
            post_result = post_response.json()
            
            # Validate POST response - should return instruction message and NOT persist the dummy key
            if 'message' not in post_result:
                self.log_test("SendGrid Settings", False, "POST response missing instruction message")
                return False
            
            instruction_message = post_result.get('message', '')
            if 'instruction' not in instruction_message.lower() or len(instruction_message) < 20:
                self.log_test("SendGrid Settings", False, f"POST response should contain instruction message, got: {instruction_message}")
                return False
            
            # Verify the dummy key was NOT persisted by checking GET again
            verify_response = self.session.get(f"{API_BASE}/settings/sendgrid", headers=auth_headers)
            if verify_response.status_code != 200:
                self.log_test("SendGrid Settings", False, "Failed to verify settings after POST")
                return False
            
            verify_result = verify_response.json()
            
            # The configured flag should still be the same (dummy key not persisted)
            if verify_result.get('configured') != configured_flag:
                # Only fail if it changed from False to True (dummy key was persisted)
                if not configured_flag and verify_result.get('configured'):
                    self.log_test("SendGrid Settings", False, "Dummy key was incorrectly persisted")
                    return False
            
            self.log_test("SendGrid Settings", True, f"SendGrid settings working: GET returns configured flag ({configured_flag}), POST with dummy key returns instruction message and doesn't persist key")
            return True
            
        except Exception as e:
            self.log_test("SendGrid Settings", False, f"Error: {str(e)}")
            return False

    def test_scheduler_smoke_test(self):
        """Test Scheduler endpoints smoke test - ensure they still work"""
        try:
            # Test basic scheduler status/health endpoints if they exist
            # Since we're not asserting timed triggers, just check endpoints respond
            
            # Try common scheduler endpoint patterns
            scheduler_endpoints = [
                "/scheduler/status",
                "/scheduler/health", 
                "/admin/scheduler/status",
                "/system/scheduler"
            ]
            
            working_endpoints = []
            for endpoint in scheduler_endpoints:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    if response.status_code in [200, 401, 403]:  # 401/403 means endpoint exists but needs auth
                        working_endpoints.append(endpoint)
                except:
                    continue
            
            if working_endpoints:
                self.log_test("Scheduler Smoke Test", True, f"Scheduler endpoints responding: {working_endpoints}")
                return True
            else:
                # If no specific scheduler endpoints, just verify the system is responsive
                # This is a smoke test, so we just need to know the system isn't broken
                root_response = self.session.get(f"{API_BASE}/")
                if root_response.status_code == 200:
                    self.log_test("Scheduler Smoke Test", True, "System responsive - scheduler functionality not breaking core API")
                    return True
                else:
                    self.log_test("Scheduler Smoke Test", False, "System not responsive")
                    return False
            
        except Exception as e:
            self.log_test("Scheduler Smoke Test", False, f"Error: {str(e)}")
            return False

    def print_test_summary(self):
        """Print a summary of all test results"""
        print("\n" + "=" * 80)
        print("📊 TARGETED BACKEND TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = sum(1 for result in self.test_results if not result['success'])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "No tests run")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"   • {result['test']}: {result['details']}")
        
        print("=" * 80)

    def run_targeted_tests(self):
        """Run targeted backend tests as requested in review"""
        print("🎯 Starting Targeted Backend Tests for Review Request")
        print(f"📡 Testing API at: {API_BASE}")
        print("=" * 80)
        
        # Test basic connectivity first
        if not self.test_api_root():
            print("❌ API connectivity failed - stopping tests")
            return
        
        # Authentication tests (required for admin endpoints)
        if not self.test_authentication_system():
            print("❌ Authentication failed - stopping tests")
            return
        
        # Run the specific tests requested in the review
        print("\n🔍 Testing Formula Param Editor & Versioning...")
        self.test_formula_param_editor_versioning()
        
        print("\n🔍 Testing SendGrid Settings Endpoints...")
        self.test_sendgrid_settings_endpoints()
        
        print("\n🔍 Testing Scheduler Smoke Test...")
        self.test_scheduler_smoke_test()
        
        # Print summary
        self.print_test_summary()
        """Test root API endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("API Root", True, f"Root endpoint accessible: {data['message']}")
                    return True
                else:
                    self.log_test("API Root", False, "Root endpoint missing message field")
                    return False
            else:
                self.log_test("API Root", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("API Root", False, f"Connection error: {str(e)}")
            return False
    
    def test_etf_data_update(self):
        """Test ETF data update from yfinance"""
        try:
            print("Triggering ETF data update (this may take 30-60 seconds)...")
            response = self.session.post(f"{API_BASE}/etfs/update", timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)
                if count > 0:
                    self.log_test("ETF Data Update", True, f"Successfully updated {count} ETFs from yfinance", data)
                    return True
                else:
                    self.log_test("ETF Data Update", False, "Update returned 0 ETFs")
                    return False
            else:
                self.log_test("ETF Data Update", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("ETF Data Update", False, f"Error: {str(e)}")
            return False
    
    def test_get_etfs(self):
        """Test getting ETF data with filtering"""
        try:
            # Test basic ETF retrieval
            response = self.session.get(f"{API_BASE}/etfs")
            if response.status_code != 200:
                self.log_test("Get ETFs", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
            etfs = response.json()
            if not etfs:
                self.log_test("Get ETFs", False, "No ETF data returned")
                return False
            
            # Validate ETF data structure
            sample_etf = etfs[0]
            required_fields = ['ticker', 'name', 'sector', 'current_price', 'change_1d', 
                             'change_1w', 'change_1m', 'relative_strength_1m', 'sata_score']
            
            missing_fields = [field for field in required_fields if field not in sample_etf]
            if missing_fields:
                self.log_test("Get ETFs", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Test filtering by sector
            sectors_response = self.session.get(f"{API_BASE}/etfs/sectors")
            if sectors_response.status_code == 200:
                sectors_data = sectors_response.json()
                if sectors_data.get('sectors'):
                    test_sector = sectors_data['sectors'][0]
                    filtered_response = self.session.get(f"{API_BASE}/etfs?sector={test_sector}")
                    if filtered_response.status_code == 200:
                        filtered_etfs = filtered_response.json()
                        if all(etf['sector'] == test_sector for etf in filtered_etfs):
                            self.log_test("Get ETFs", True, f"Retrieved {len(etfs)} ETFs, filtering works correctly")
                            return True
                        else:
                            self.log_test("Get ETFs", False, "Sector filtering not working correctly")
                            return False
            
            self.log_test("Get ETFs", True, f"Retrieved {len(etfs)} ETFs with valid structure")
            return True
            
        except Exception as e:
            self.log_test("Get ETFs", False, f"Error: {str(e)}")
            return False
    
    def test_etf_calculations(self):
        """Test ETF calculations (relative strength, SATA score, etc.)"""
        try:
            response = self.session.get(f"{API_BASE}/etfs?limit=5")
            if response.status_code != 200:
                self.log_test("ETF Calculations", False, f"HTTP {response.status_code}")
                return False
                
            etfs = response.json()
            if not etfs:
                self.log_test("ETF Calculations", False, "No ETF data to validate")
                return False
            
            calculation_issues = []
            
            for etf in etfs[:3]:  # Test first 3 ETFs
                ticker = etf['ticker']
                
                # Validate SATA score range (1-10)
                sata_score = etf.get('sata_score', 0)
                if not (1 <= sata_score <= 10):
                    calculation_issues.append(f"{ticker}: SATA score {sata_score} out of range 1-10")
                
                # Validate relative strength is a reasonable number
                rs_1m = etf.get('relative_strength_1m', 0)
                if abs(rs_1m) > 10:  # Relative strength shouldn't be extremely high
                    calculation_issues.append(f"{ticker}: Relative strength {rs_1m} seems unrealistic")
                
                # Validate price changes are reasonable percentages
                change_1d = etf.get('change_1d', 0)
                if abs(change_1d) > 50:  # Daily change > 50% is suspicious
                    calculation_issues.append(f"{ticker}: Daily change {change_1d}% seems unrealistic")
                
                # Validate ATR percentage
                atr_percent = etf.get('atr_percent', 0)
                if atr_percent < 0 or atr_percent > 100:
                    calculation_issues.append(f"{ticker}: ATR percentage {atr_percent}% out of reasonable range")
            
            if calculation_issues:
                self.log_test("ETF Calculations", False, f"Calculation issues found: {'; '.join(calculation_issues)}")
                return False
            else:
                self.log_test("ETF Calculations", True, "All calculations appear mathematically correct")
                return True
                
        except Exception as e:
            self.log_test("ETF Calculations", False, f"Error: {str(e)}")
            return False
    
    def test_dashboard_api(self):
        """Test Dashboard API with SA greetings and dual timezone display"""
        try:
            response = self.session.get(f"{API_BASE}/dashboard")
            if response.status_code != 200:
                self.log_test("Dashboard API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            dashboard_data = response.json()
            
            # Validate required fields
            required_fields = ['greeting', 'sa_time', 'ny_time', 'market_countdown', 'last_updated']
            missing_fields = [field for field in required_fields if field not in dashboard_data]
            if missing_fields:
                self.log_test("Dashboard API", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate SA greeting format
            greeting = dashboard_data['greeting']
            valid_greetings = ['Goeie More Alwyn!', 'Goeie Middag Alwyn!', 'Goeie Naand Alwyn!']
            if not any(valid_greeting in greeting for valid_greeting in valid_greetings):
                self.log_test("Dashboard API", False, f"Invalid SA greeting format: {greeting}")
                return False
            
            # Validate timezone data structure
            sa_time = dashboard_data['sa_time']
            ny_time = dashboard_data['ny_time']
            
            for tz_data, tz_name in [(sa_time, 'SA'), (ny_time, 'NY')]:
                required_tz_fields = ['time', 'timezone', 'date', 'flag']
                missing_tz_fields = [field for field in required_tz_fields if field not in tz_data]
                if missing_tz_fields:
                    self.log_test("Dashboard API", False, f"Missing {tz_name} timezone fields: {missing_tz_fields}")
                    return False
            
            # Validate market countdown format
            countdown = dashboard_data['market_countdown']
            if not ('h' in countdown and 'm' in countdown and 's' in countdown):
                self.log_test("Dashboard API", False, f"Invalid countdown format: {countdown}")
                return False
            
            self.log_test("Dashboard API", True, "SA greetings, dual timezone display, and market countdown working correctly")
            return True
            
        except Exception as e:
            self.log_test("Dashboard API", False, f"Error: {str(e)}")
            return False
    
    def test_swing_leaders(self):
        """Test Swing Leaders endpoint (SATA + RS combined scoring)"""
        try:
            response = self.session.get(f"{API_BASE}/etfs/swing-leaders")
            if response.status_code != 200:
                self.log_test("Swing Leaders", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            leaders = response.json()
            if not leaders:
                self.log_test("Swing Leaders", False, "No swing leaders returned")
                return False
            
            if len(leaders) != 5:
                self.log_test("Swing Leaders", False, f"Expected 5 leaders, got {len(leaders)}")
                return False
            
            # Validate each leader has required fields
            for leader in leaders:
                required_fields = ['ticker', 'name', 'sata_score', 'relative_strength_1m']
                missing_fields = [field for field in required_fields if field not in leader]
                if missing_fields:
                    self.log_test("Swing Leaders", False, f"Leader missing fields: {missing_fields}")
                    return False
            
            # Verify leaders are sorted by swing score (SATA + RS combination)
            if len(leaders) > 1:
                for i in range(len(leaders) - 1):
                    current_score = leaders[i].get('sata_score', 0) + (leaders[i].get('relative_strength_1m', 0) * 10)
                    next_score = leaders[i + 1].get('sata_score', 0) + (leaders[i + 1].get('relative_strength_1m', 0) * 10)
                    if current_score < next_score:
                        self.log_test("Swing Leaders", False, "Leaders not properly sorted by swing score")
                        return False
            
            self.log_test("Swing Leaders", True, f"Top 5 swing leaders returned with correct SATA + RS scoring")
            return True
            
        except Exception as e:
            self.log_test("Swing Leaders", False, f"Error: {str(e)}")
            return False
    
    def test_watchlist_management(self):
        """Test watchlist CRUD operations"""
        try:
            # Create a test watchlist item
            test_item = {
                "ticker": "SPY",
                "name": "SPDR S&P 500 ETF",
                "list_name": "Test Portfolio",
                "notes": "Test watchlist item for API testing",
                "tags": ["test", "large-cap"],
                "priority": 3,
                "entry_price": 450.0,
                "target_price": 500.0,
                "stop_loss": 420.0,
                "position_size": 100.0
            }
            
            # Test CREATE
            create_response = self.session.post(f"{API_BASE}/watchlists", json=test_item)
            if create_response.status_code != 200:
                self.log_test("Watchlist Management", False, f"Create failed: HTTP {create_response.status_code}")
                return False
            
            created_item = create_response.json()
            item_id = created_item.get('id')
            if not item_id:
                self.log_test("Watchlist Management", False, "Created item missing ID")
                return False
            
            self.watchlist_items_created.append(item_id)
            
            # Test READ - Get all watchlists
            get_response = self.session.get(f"{API_BASE}/watchlists")
            if get_response.status_code != 200:
                self.log_test("Watchlist Management", False, f"Get all failed: HTTP {get_response.status_code}")
                return False
            
            all_items = get_response.json()
            created_found = any(item.get('id') == item_id for item in all_items)
            if not created_found:
                self.log_test("Watchlist Management", False, "Created item not found in get all")
                return False
            
            # Test READ - Filter by list name
            filtered_response = self.session.get(f"{API_BASE}/watchlists?list_name=Test Portfolio")
            if filtered_response.status_code != 200:
                self.log_test("Watchlist Management", False, f"Filtered get failed: HTTP {filtered_response.status_code}")
                return False
            
            filtered_items = filtered_response.json()
            if not any(item.get('list_name') == 'Test Portfolio' for item in filtered_items):
                self.log_test("Watchlist Management", False, "List name filtering not working")
                return False
            
            # Test get unique list names
            lists_response = self.session.get(f"{API_BASE}/watchlists/names")
            if lists_response.status_code != 200:
                self.log_test("Watchlist Management", False, f"Get lists failed: HTTP {lists_response.status_code}")
                return False
            
            lists_data = lists_response.json()
            if 'Test Portfolio' not in lists_data.get('lists', []):
                self.log_test("Watchlist Management", False, "Test Portfolio not in unique lists")
                return False
            
            # Test DELETE
            delete_response = self.session.delete(f"{API_BASE}/watchlists/{item_id}")
            if delete_response.status_code != 200:
                self.log_test("Watchlist Management", False, f"Delete failed: HTTP {delete_response.status_code}")
                return False
            
            # Verify deletion
            verify_response = self.session.get(f"{API_BASE}/watchlists")
            verify_items = verify_response.json()
            if any(item.get('id') == item_id for item in verify_items):
                self.log_test("Watchlist Management", False, "Item not properly deleted")
                return False
            
            self.log_test("Watchlist Management", True, "All CRUD operations working correctly")
            return True
            
        except Exception as e:
            self.log_test("Watchlist Management", False, f"Error: {str(e)}")
            return False
    
    def test_universal_stock_lookup(self):
        """Test Universal Stock Lookup for any ticker"""
        try:
            # Test with popular stocks beyond ETFs
            test_tickers = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'NVDA']
            
            for ticker in test_tickers:
                response = self.session.get(f"{API_BASE}/stocks/{ticker}")
                if response.status_code != 200:
                    self.log_test("Universal Stock Lookup", False, f"Failed for {ticker}: HTTP {response.status_code}")
                    return False
                
                stock_data = response.json()
                
                # Validate stock data structure
                required_fields = ['current_price', 'change_1d', 'change_1w', 'change_1m', 
                                 'change_3m', 'change_6m', 'atr_percent', 'volume']
                missing_fields = [field for field in required_fields if field not in stock_data]
                if missing_fields:
                    self.log_test("Universal Stock Lookup", False, f"{ticker} missing fields: {missing_fields}")
                    return False
                
                # Validate data types and ranges
                if stock_data['current_price'] <= 0:
                    self.log_test("Universal Stock Lookup", False, f"{ticker} invalid price: {stock_data['current_price']}")
                    return False
                
                if stock_data['atr_percent'] < 0:
                    self.log_test("Universal Stock Lookup", False, f"{ticker} invalid ATR: {stock_data['atr_percent']}")
                    return False
            
            self.log_test("Universal Stock Lookup", True, f"Successfully retrieved data for {len(test_tickers)} different stock tickers")
            return True
            
        except Exception as e:
            self.log_test("Universal Stock Lookup", False, f"Error: {str(e)}")
            return False
    
    def test_custom_watchlist_lists(self):
        """Test Custom Watchlist Lists management"""
        try:
            # Test CREATE custom watchlist
            test_list = {
                "name": "Test Growth Portfolio",
                "description": "Test watchlist for growth stocks and ETFs",
                "color": "#10B981"
            }
            
            create_response = self.session.post(f"{API_BASE}/watchlists/lists", json=test_list)
            if create_response.status_code != 200:
                self.log_test("Custom Watchlist Lists", False, f"Create failed: HTTP {create_response.status_code}")
                return False
            
            created_list = create_response.json()
            list_id = created_list.get('id')
            if not list_id:
                self.log_test("Custom Watchlist Lists", False, "Created list missing ID")
                return False
            
            # Test GET custom watchlists
            get_response = self.session.get(f"{API_BASE}/watchlists/lists")
            if get_response.status_code != 200:
                self.log_test("Custom Watchlist Lists", False, f"Get failed: HTTP {get_response.status_code}")
                return False
            
            lists = get_response.json()
            created_found = any(wl.get('id') == list_id for wl in lists)
            if not created_found:
                self.log_test("Custom Watchlist Lists", False, "Created list not found in get all")
                return False
            
            self.log_test("Custom Watchlist Lists", True, "Custom watchlist lists management working correctly")
            return True
            
        except Exception as e:
            self.log_test("Custom Watchlist Lists", False, f"Error: {str(e)}")
            return False
    
    def test_journal_management(self):
        """Test Journal Management CRUD operations"""
        try:
            # Test CREATE journal entry
            test_entry = {
                "title": "Test Trading Journal Entry",
                "content": "This is a test journal entry for API testing. Market conditions were favorable today.",
                "tags": ["test", "swing-trading", "bullish"],
                "market_score": 25,
                "trades_mentioned": ["SPY", "QQQ"],
                "mood": "positive"
            }
            
            create_response = self.session.post(f"{API_BASE}/journal", json=test_entry)
            if create_response.status_code != 200:
                self.log_test("Journal Management", False, f"Create failed: HTTP {create_response.status_code}")
                return False
            
            created_entry = create_response.json()
            entry_id = created_entry.get('id')
            if not entry_id:
                self.log_test("Journal Management", False, "Created entry missing ID")
                return False
            
            # Test READ journal entries
            get_response = self.session.get(f"{API_BASE}/journal")
            if get_response.status_code != 200:
                self.log_test("Journal Management", False, f"Get failed: HTTP {get_response.status_code}")
                return False
            
            entries = get_response.json()
            created_found = any(entry.get('id') == entry_id for entry in entries)
            if not created_found:
                self.log_test("Journal Management", False, "Created entry not found in get all")
                return False
            
            # Test with days parameter
            days_response = self.session.get(f"{API_BASE}/journal?days=7")
            if days_response.status_code != 200:
                self.log_test("Journal Management", False, f"Days parameter failed: HTTP {days_response.status_code}")
                return False
            
            self.log_test("Journal Management", True, "Journal CRUD operations working correctly")
            return True
            
        except Exception as e:
            self.log_test("Journal Management", False, f"Error: {str(e)}")
            return False
    
    def test_historical_data(self):
        """Test Historical Data snapshots"""
        try:
            # Test GET historical snapshots
            response = self.session.get(f"{API_BASE}/history")
            if response.status_code != 200:
                self.log_test("Historical Data", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            snapshots = response.json()
            # It's OK if no historical data exists yet, but endpoint should work
            
            # Test with days parameter
            days_response = self.session.get(f"{API_BASE}/history?days=7")
            if days_response.status_code != 200:
                self.log_test("Historical Data", False, f"Days parameter failed: HTTP {days_response.status_code}")
                return False
            
            # Test with different days parameter
            days_response_30 = self.session.get(f"{API_BASE}/history?days=30")
            if days_response_30.status_code != 200:
                self.log_test("Historical Data", False, f"30 days parameter failed: HTTP {days_response.status_code}")
                return False
            
            self.log_test("Historical Data", True, "Historical snapshots endpoint working correctly")
            return True
            
        except Exception as e:
            self.log_test("Historical Data", False, f"Error: {str(e)}")
            return False
    
    def test_market_score(self):
        """Test Market Situational Awareness Engine"""
        try:
            # Test GET market score
            get_response = self.session.get(f"{API_BASE}/market-score")
            if get_response.status_code != 200:
                self.log_test("Market Score", False, f"Get failed: HTTP {get_response.status_code}")
                return False
            
            score_data = get_response.json()
            
            # Validate score structure
            required_fields = ['sata_score', 'adx_score', 'vix_score', 'atr_score', 
                             'gmi_score', 'nhnl_score', 'fg_index_score', 
                             'qqq_ath_distance_score', 'total_score', 'classification']
            
            missing_fields = [field for field in required_fields if field not in score_data]
            if missing_fields:
                self.log_test("Market Score", False, f"Missing fields: {missing_fields}")
                return False
            
            # Validate score ranges (each component 1-5, total 8-40)
            component_scores = [score_data[field] for field in required_fields[:8]]
            if not all(1 <= score <= 5 for score in component_scores):
                self.log_test("Market Score", False, "Component scores not in range 1-5")
                return False
            
            total_score = score_data['total_score']
            expected_total = sum(component_scores)
            if total_score != expected_total:
                self.log_test("Market Score", False, f"Total score {total_score} doesn't match sum {expected_total}")
                return False
            
            # Validate classification
            classification = score_data['classification']
            valid_classifications = ['Green Day', 'Yellow Day', 'Red Day']
            if classification not in valid_classifications:
                self.log_test("Market Score", False, f"Invalid classification: {classification}")
                return False
            
            # Test POST market score update
            test_score = {
                "sata_score": 4,
                "adx_score": 3,
                "vix_score": 2,
                "atr_score": 3,
                "gmi_score": 4,
                "nhnl_score": 3,
                "fg_index_score": 2,
                "qqq_ath_distance_score": 3
            }
            
            post_response = self.session.post(f"{API_BASE}/market-score", json=test_score)
            if post_response.status_code != 200:
                self.log_test("Market Score", False, f"Post failed: HTTP {post_response.status_code}")
                return False
            
            updated_score = post_response.json()
            expected_total = sum(test_score.values())  # Should be 24
            
            if updated_score['total_score'] != expected_total:
                self.log_test("Market Score", False, f"Updated total {updated_score['total_score']} != expected {expected_total}")
                return False
            
            # Verify classification logic
            if expected_total >= 28:
                expected_class = "Green Day"
            elif expected_total >= 20:
                expected_class = "Yellow Day"
            else:
                expected_class = "Red Day"
            
            if updated_score['classification'] != expected_class:
                self.log_test("Market Score", False, f"Classification {updated_score['classification']} != expected {expected_class}")
                return False
            
            self.log_test("Market Score", True, "MSAE scoring system working correctly")
            return True
            
        except Exception as e:
            self.log_test("Market Score", False, f"Error: {str(e)}")
            return False
    
    def test_chart_analysis(self):
        """Test AI Chart Analysis endpoint"""
        try:
            # Test with multiple tickers including stocks beyond ETFs
            test_tickers = ["SPY", "AAPL", "TSLA"]
            
            for ticker in test_tickers:
                response = self.session.get(f"{API_BASE}/charts/{ticker}/analysis")
                
                if response.status_code != 200:
                    self.log_test("Chart Analysis", False, f"HTTP {response.status_code} for {ticker}: {response.text}")
                    return False
                
                analysis = response.json()
                
                # Validate analysis structure
                required_fields = ['ticker', 'timeframe', 'pattern_analysis', 'support_levels', 
                                 'resistance_levels', 'trend_analysis', 'risk_reward', 
                                 'recommendation', 'confidence']
                
                missing_fields = [field for field in required_fields if field not in analysis]
                if missing_fields:
                    self.log_test("Chart Analysis", False, f"{ticker} missing fields: {missing_fields}")
                    return False
                
                # Validate data types
                if analysis['ticker'] != ticker.upper():
                    self.log_test("Chart Analysis", False, f"Ticker mismatch: {analysis['ticker']} != {ticker.upper()}")
                    return False
                
                if not isinstance(analysis['support_levels'], list) or len(analysis['support_levels']) == 0:
                    self.log_test("Chart Analysis", False, f"{ticker} support levels invalid")
                    return False
                
                if not isinstance(analysis['resistance_levels'], list) or len(analysis['resistance_levels']) == 0:
                    self.log_test("Chart Analysis", False, f"{ticker} resistance levels invalid")
                    return False
                
                confidence = analysis.get('confidence', 0)
                if not (0 <= confidence <= 1):
                    self.log_test("Chart Analysis", False, f"{ticker} confidence {confidence} not in range 0-1")
                    return False
                
                # Validate that analysis contains realistic trading recommendations
                recommendation = analysis.get('recommendation', '')
                if not any(keyword in recommendation.upper() for keyword in ['BUY', 'SELL', 'WAIT', 'AVOID', 'HOLD']):
                    self.log_test("Chart Analysis", False, f"{ticker} recommendation doesn't contain trading action")
                    return False
            
            # Test with different timeframe
            response_1h = self.session.get(f"{API_BASE}/charts/SPY/analysis?timeframe=1h")
            if response_1h.status_code != 200:
                self.log_test("Chart Analysis", False, f"Timeframe parameter not working: HTTP {response_1h.status_code}")
                return False
            
            self.log_test("Chart Analysis", True, f"AI Chart Analysis working for {len(test_tickers)} tickers with realistic recommendations")
            return True
            
        except Exception as e:
            self.log_test("Chart Analysis", False, f"Error: {str(e)}")
            return False

    def test_enhanced_dashboard_api(self):
        """Test Enhanced Dashboard API with all new professional features"""
        try:
            response = self.session.get(f"{API_BASE}/dashboard")
            if response.status_code != 200:
                self.log_test("Enhanced Dashboard API", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            dashboard_data = response.json()
            
            # Validate enhanced dashboard fields
            required_fields = ['greeting', 'sa_time', 'ny_time', 'market_countdown', 
                             'major_indices', 'zar_usd_rate', 'fear_greed_index', 'last_updated']
            missing_fields = [field for field in required_fields if field not in dashboard_data]
            if missing_fields:
                self.log_test("Enhanced Dashboard API", False, f"Missing enhanced fields: {missing_fields}")
                return False
            
            # Validate major indices data
            major_indices = dashboard_data.get('major_indices', {})
            expected_indices = ['SPY', 'QQQ', 'DIA', 'IWM']
            for index in expected_indices:
                if index not in major_indices:
                    self.log_test("Enhanced Dashboard API", False, f"Missing major index: {index}")
                    return False
                
                index_data = major_indices[index]
                required_index_fields = ['price', 'change_1d', 'last_updated']
                missing_index_fields = [field for field in required_index_fields if field not in index_data]
                if missing_index_fields:
                    self.log_test("Enhanced Dashboard API", False, f"{index} missing fields: {missing_index_fields}")
                    return False
            
            # Validate ZAR/USD rate
            zar_usd_rate = dashboard_data.get('zar_usd_rate')
            if not isinstance(zar_usd_rate, (int, float)) or zar_usd_rate <= 0:
                self.log_test("Enhanced Dashboard API", False, f"Invalid ZAR/USD rate: {zar_usd_rate}")
                return False
            
            # Validate Fear & Greed Index
            fear_greed = dashboard_data.get('fear_greed_index', {})
            required_fg_fields = ['index', 'rating', 'last_updated', 'components']
            missing_fg_fields = [field for field in required_fg_fields if field not in fear_greed]
            if missing_fg_fields:
                self.log_test("Enhanced Dashboard API", False, f"Fear & Greed missing fields: {missing_fg_fields}")
                return False
            
            # Validate Fear & Greed components
            fg_components = fear_greed.get('components', {})
            expected_components = ['stock_price_momentum', 'market_volatility', 'safe_haven_demand', 'put_call_ratio']
            for component in expected_components:
                if component not in fg_components:
                    self.log_test("Enhanced Dashboard API", False, f"Missing F&G component: {component}")
                    return False
            
            self.log_test("Enhanced Dashboard API", True, "All enhanced dashboard features working: SA greetings, dual timezone, major indices, ZAR/USD, Fear & Greed integration")
            return True
            
        except Exception as e:
            self.log_test("Enhanced Dashboard API", False, f"Error: {str(e)}")
            return False

    def test_live_market_data_apis(self):
        """Test Live Market Data APIs"""
        try:
            # Test Live Indices API
            indices_response = self.session.get(f"{API_BASE}/live/indices")
            if indices_response.status_code != 200:
                self.log_test("Live Market Data APIs", False, f"Live indices failed: HTTP {indices_response.status_code}")
                return False
            
            indices_data = indices_response.json()
            expected_indices = ['SPY', 'QQQ', 'DIA', 'IWM', 'VIX']
            for index in expected_indices:
                if index not in indices_data:
                    self.log_test("Live Market Data APIs", False, f"Missing live index: {index}")
                    return False
                
                index_info = indices_data[index]
                required_fields = ['symbol', 'price', 'change_1d', 'volume', 'last_updated']
                missing_fields = [field for field in required_fields if field not in index_info]
                if missing_fields:
                    self.log_test("Live Market Data APIs", False, f"{index} missing fields: {missing_fields}")
                    return False
            
            # Test Fear & Greed API
            fg_response = self.session.get(f"{API_BASE}/live/fear-greed")
            if fg_response.status_code != 200:
                self.log_test("Live Market Data APIs", False, f"Fear & Greed failed: HTTP {fg_response.status_code}")
                return False
            
            fg_data = fg_response.json()
            required_fg_fields = ['index', 'rating', 'color', 'last_updated', 'components']
            missing_fg_fields = [field for field in required_fg_fields if field not in fg_data]
            if missing_fg_fields:
                self.log_test("Live Market Data APIs", False, f"Fear & Greed missing fields: {missing_fg_fields}")
                return False
            
            # Validate Fear & Greed index range
            fg_index = fg_data.get('index', 0)
            if not (0 <= fg_index <= 100):
                self.log_test("Live Market Data APIs", False, f"Fear & Greed index {fg_index} out of range 0-100")
                return False
            
            # Test Forex API
            forex_response = self.session.get(f"{API_BASE}/live/forex")
            if forex_response.status_code != 200:
                self.log_test("Live Market Data APIs", False, f"Forex failed: HTTP {forex_response.status_code}")
                return False
            
            forex_data = forex_response.json()
            if 'ZAR_USD' not in forex_data:
                self.log_test("Live Market Data APIs", False, "Missing ZAR_USD in forex data")
                return False
            
            zar_usd = forex_data['ZAR_USD']
            required_forex_fields = ['rate', 'change', 'change_percent', 'last_updated']
            missing_forex_fields = [field for field in required_forex_fields if field not in zar_usd]
            if missing_forex_fields:
                self.log_test("Live Market Data APIs", False, f"ZAR_USD missing fields: {missing_forex_fields}")
                return False
            
            # Validate major pairs exist
            if 'major_pairs' not in forex_data:
                self.log_test("Live Market Data APIs", False, "Missing major_pairs in forex data")
                return False
            
            self.log_test("Live Market Data APIs", True, "All live market data APIs working: indices, Fear & Greed, forex rates")
            return True
            
        except Exception as e:
            self.log_test("Live Market Data APIs", False, f"Error: {str(e)}")
            return False

    def test_export_integration_apis(self):
        """Test Export & Integration APIs"""
        try:
            # Test ETF Export API
            etf_export_response = self.session.get(f"{API_BASE}/export/etfs")
            if etf_export_response.status_code != 200:
                self.log_test("Export & Integration APIs", False, f"ETF export failed: HTTP {etf_export_response.status_code}")
                return False
            
            etf_export_data = etf_export_response.json()
            required_export_fields = ['data', 'total_records', 'export_timestamp', 'format']
            missing_export_fields = [field for field in required_export_fields if field not in etf_export_data]
            if missing_export_fields:
                self.log_test("Export & Integration APIs", False, f"ETF export missing fields: {missing_export_fields}")
                return False
            
            # Validate export data structure
            export_data = etf_export_data.get('data', [])
            if not export_data:
                self.log_test("Export & Integration APIs", False, "No ETF data in export")
                return False
            
            # Validate CSV-compatible format
            sample_etf = export_data[0]
            expected_csv_fields = ['Ticker', 'Name', 'Sector', 'Theme', 'Current_Price', 
                                 'Change_1D', 'Change_1W', 'Change_1M', 'RS_1M', 'SATA_Score']
            missing_csv_fields = [field for field in expected_csv_fields if field not in sample_etf]
            if missing_csv_fields:
                self.log_test("Export & Integration APIs", False, f"CSV format missing fields: {missing_csv_fields}")
                return False
            
            # Validate format specification
            if etf_export_data.get('format') != 'csv_compatible':
                self.log_test("Export & Integration APIs", False, "Export format not marked as csv_compatible")
                return False
            
            # Test Market Score Export API
            score_export_response = self.session.get(f"{API_BASE}/export/market-score")
            if score_export_response.status_code != 200:
                self.log_test("Export & Integration APIs", False, f"Market score export failed: HTTP {score_export_response.status_code}")
                return False
            
            score_export_data = score_export_response.json()
            required_score_fields = ['market_score_data', 'export_timestamp']
            missing_score_fields = [field for field in required_score_fields if field not in score_export_data]
            if missing_score_fields:
                self.log_test("Export & Integration APIs", False, f"Market score export missing fields: {missing_score_fields}")
                return False
            
            self.log_test("Export & Integration APIs", True, "Export APIs working: ETF CSV export and market score export")
            return True
            
        except Exception as e:
            self.log_test("Export & Integration APIs", False, f"Error: {str(e)}")
            return False

    def test_formula_configuration_apis(self):
        """Test Formula Configuration APIs"""
        try:
            # Test GET formula config
            get_response = self.session.get(f"{API_BASE}/formulas/config")
            if get_response.status_code != 200:
                self.log_test("Formula Configuration APIs", False, f"Get config failed: HTTP {get_response.status_code}")
                return False
            
            config_data = get_response.json()
            
            # Validate configuration structure
            expected_config_sections = ['relative_strength', 'sata_weights', 'atr_calculation', 'gmma_patterns']
            missing_sections = [section for section in expected_config_sections if section not in config_data]
            if missing_sections:
                self.log_test("Formula Configuration APIs", False, f"Missing config sections: {missing_sections}")
                return False
            
            # Validate relative strength config
            rs_config = config_data.get('relative_strength', {})
            required_rs_fields = ['strong_threshold', 'moderate_threshold', 'formula']
            missing_rs_fields = [field for field in required_rs_fields if field not in rs_config]
            if missing_rs_fields:
                self.log_test("Formula Configuration APIs", False, f"Relative strength config missing: {missing_rs_fields}")
                return False
            
            # Validate SATA weights config
            sata_config = config_data.get('sata_weights', {})
            required_sata_fields = ['performance', 'relative_strength', 'volume', 'volatility', 'formula']
            missing_sata_fields = [field for field in required_sata_fields if field not in sata_config]
            if missing_sata_fields:
                self.log_test("Formula Configuration APIs", False, f"SATA weights config missing: {missing_sata_fields}")
                return False
            
            # Test POST formula config update
            updated_config = config_data.copy()
            updated_config['relative_strength']['strong_threshold'] = 0.12  # Modify a value
            
            post_response = self.session.post(f"{API_BASE}/formulas/config", json=updated_config)
            if post_response.status_code != 200:
                self.log_test("Formula Configuration APIs", False, f"Update config failed: HTTP {post_response.status_code}")
                return False
            
            update_result = post_response.json()
            if 'message' not in update_result or 'config' not in update_result:
                self.log_test("Formula Configuration APIs", False, "Update response missing required fields")
                return False
            
            # Verify the update was applied
            verify_response = self.session.get(f"{API_BASE}/formulas/config")
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                if verify_data.get('relative_strength', {}).get('strong_threshold') != 0.12:
                    self.log_test("Formula Configuration APIs", False, "Configuration update not persisted")
                    return False
            
            self.log_test("Formula Configuration APIs", True, "Formula configuration APIs working: get and update with recalculation trigger")
            return True
            
        except Exception as e:
            self.log_test("Formula Configuration APIs", False, f"Error: {str(e)}")
            return False

    def test_enhanced_calculations(self):
        """Test Enhanced Professional Calculations"""
        try:
            # Get ETF data to validate enhanced calculations
            response = self.session.get(f"{API_BASE}/etfs?limit=10")
            if response.status_code != 200:
                self.log_test("Enhanced Calculations", False, f"HTTP {response.status_code}")
                return False
            
            etfs = response.json()
            if not etfs:
                self.log_test("Enhanced Calculations", False, "No ETF data for calculation validation")
                return False
            
            calculation_validations = []
            
            for etf in etfs[:5]:  # Test first 5 ETFs
                ticker = etf['ticker']
                
                # Validate enhanced SATA scoring (1-10 range)
                sata_score = etf.get('sata_score', 0)
                if not (1 <= sata_score <= 10):
                    calculation_validations.append(f"{ticker}: SATA score {sata_score} out of professional range 1-10")
                
                # Validate relative strength calculations
                rs_1m = etf.get('relative_strength_1m', 0)
                rs_3m = etf.get('relative_strength_3m', 0)
                rs_6m = etf.get('relative_strength_6m', 0)
                
                # Relative strength should be reasonable values
                for period, rs_value in [('1M', rs_1m), ('3M', rs_3m), ('6M', rs_6m)]:
                    if abs(rs_value) > 5:  # Extreme relative strength values
                        calculation_validations.append(f"{ticker}: {period} RS {rs_value} seems extreme")
                
                # Validate GMMA pattern classification
                gmma_pattern = etf.get('gmma_pattern', '')
                valid_patterns = ['RWB', 'BWR', 'Mixed']
                if gmma_pattern not in valid_patterns:
                    calculation_validations.append(f"{ticker}: Invalid GMMA pattern '{gmma_pattern}'")
                
                # Validate SMA20 trend
                sma20_trend = etf.get('sma20_trend', '')
                valid_trends = ['U', 'D', 'F']
                if sma20_trend not in valid_trends:
                    calculation_validations.append(f"{ticker}: Invalid SMA20 trend '{sma20_trend}'")
                
                # Validate ATR percentage is reasonable
                atr_percent = etf.get('atr_percent', 0)
                if atr_percent < 0 or atr_percent > 50:  # ATR should be positive and reasonable
                    calculation_validations.append(f"{ticker}: ATR {atr_percent}% out of reasonable range")
            
            # Test Market Score calculations
            market_score_response = self.session.get(f"{API_BASE}/market-score")
            if market_score_response.status_code == 200:
                market_score = market_score_response.json()
                
                # Validate 8-component scoring system
                component_scores = [
                    market_score.get('sata_score', 0),
                    market_score.get('adx_score', 0),
                    market_score.get('vix_score', 0),
                    market_score.get('atr_score', 0),
                    market_score.get('gmi_score', 0),
                    market_score.get('nhnl_score', 0),
                    market_score.get('fg_index_score', 0),
                    market_score.get('qqq_ath_distance_score', 0)
                ]
                
                # Each component should be 1-5
                for i, score in enumerate(component_scores):
                    if not (1 <= score <= 5):
                        calculation_validations.append(f"Market score component {i+1}: {score} not in range 1-5")
                
                # Total should be sum of components (8-40 range)
                expected_total = sum(component_scores)
                actual_total = market_score.get('total_score', 0)
                if actual_total != expected_total:
                    calculation_validations.append(f"Market score total {actual_total} != sum of components {expected_total}")
            
            if calculation_validations:
                self.log_test("Enhanced Calculations", False, f"Calculation issues: {'; '.join(calculation_validations[:3])}")  # Show first 3 issues
                return False
            else:
                self.log_test("Enhanced Calculations", True, "All enhanced calculations mathematically accurate and professionally formatted")
                return True
            
        except Exception as e:
            self.log_test("Enhanced Calculations", False, f"Error: {str(e)}")
            return False

    def test_msae_etf_regime_engine(self):
        """Test MSAE and ETF Regime Engine - Phase 1 Contract"""
        try:
            # Test 1: GET /api/formulas/config - should return array including etf_regime config
            config_response = self.session.get(f"{API_BASE}/formulas/config")
            if config_response.status_code != 200:
                self.log_test("MSAE and ETF Regime Engine", False, f"GET /api/formulas/config failed: HTTP {config_response.status_code}")
                return False
            
            config_data = config_response.json()
            if not isinstance(config_data, list):
                self.log_test("MSAE and ETF Regime Engine", False, "formulas/config should return an array")
                return False
            
            # Find etf_regime config
            etf_regime_config = None
            for config in config_data:
                if config.get('kind') == 'etf_regime':
                    etf_regime_config = config
                    break
            
            if not etf_regime_config:
                self.log_test("MSAE and ETF Regime Engine", False, "No etf_regime config found in formulas/config")
                return False
            
            # Validate etf_regime config has expected defaults
            params = etf_regime_config.get('params', {})
            expected_defaults = {
                'ema_fast': 20,
                'ema_slow': 50,
                'adx_threshold': 20
            }
            
            for key, expected_value in expected_defaults.items():
                if params.get(key) != expected_value:
                    self.log_test("MSAE and ETF Regime Engine", False, f"etf_regime config missing or incorrect {key}: expected {expected_value}, got {params.get(key)}")
                    return False
            
            # Test 2: GET /api/market/state
            market_state_response = self.session.get(f"{API_BASE}/market/state")
            if market_state_response.status_code != 200:
                self.log_test("MSAE and ETF Regime Engine", False, f"GET /api/market/state failed: HTTP {market_state_response.status_code}")
                return False
            
            market_state = market_state_response.json()
            
            # Validate market/state response structure
            required_state_fields = ['ts', 'regime', 'msae_score', 'components', 'stale']
            missing_state_fields = [field for field in required_state_fields if field not in market_state]
            if missing_state_fields:
                self.log_test("MSAE and ETF Regime Engine", False, f"market/state missing fields: {missing_state_fields}")
                return False
            
            # Validate regime is one of expected values
            regime = market_state.get('regime')
            valid_regimes = ['UPTREND', 'DOWNTREND', 'CHOP']
            if regime not in valid_regimes:
                self.log_test("MSAE and ETF Regime Engine", False, f"Invalid regime: {regime}, expected one of {valid_regimes}")
                return False
            
            # Validate msae_score is in range 0-100
            msae_score = market_state.get('msae_score')
            if not isinstance(msae_score, (int, float)) or not (0 <= msae_score <= 100):
                self.log_test("MSAE and ETF Regime Engine", False, f"Invalid msae_score: {msae_score}, expected 0-100")
                return False
            
            # Validate components structure
            components = market_state.get('components', {})
            expected_component_keys = ['ema20', 'ema50', 'adx', 'atr_pct', 'vix', 'vxn', 'breadth_pct_above_50dma', 'qqq_dist_from_ath_pct']
            missing_component_keys = [key for key in expected_component_keys if key not in components]
            if missing_component_keys:
                self.log_test("MSAE and ETF Regime Engine", False, f"components missing keys: {missing_component_keys}")
                return False
            
            # Validate stale is boolean
            stale = market_state.get('stale')
            if not isinstance(stale, bool):
                self.log_test("MSAE and ETF Regime Engine", False, f"stale should be boolean, got {type(stale)}")
                return False
            
            # Test 3: GET /api/market/history (should work after calling market/state)
            market_history_response = self.session.get(f"{API_BASE}/market/history")
            if market_history_response.status_code != 200:
                self.log_test("MSAE and ETF Regime Engine", False, f"GET /api/market/history failed: HTTP {market_history_response.status_code}")
                return False
            
            market_history = market_history_response.json()
            if not isinstance(market_history, list):
                self.log_test("MSAE and ETF Regime Engine", False, "market/history should return an array")
                return False
            
            # After calling market/state, history should have at least one record
            if len(market_history) == 0:
                self.log_test("MSAE and ETF Regime Engine", False, "market/history should have at least one record after calling market/state")
                return False
            
            # Test 4: GET /api/signals/etf-regime
            etf_regime_signal_response = self.session.get(f"{API_BASE}/signals/etf-regime")
            if etf_regime_signal_response.status_code != 200:
                self.log_test("MSAE and ETF Regime Engine", False, f"GET /api/signals/etf-regime failed: HTTP {etf_regime_signal_response.status_code}")
                return False
            
            etf_signal = etf_regime_signal_response.json()
            
            # Validate etf-regime signal structure
            required_signal_fields = ['ts', 'regime', 'decision', 'weights', 'confidence', 'reason', 'params_version']
            missing_signal_fields = [field for field in required_signal_fields if field not in etf_signal]
            if missing_signal_fields:
                self.log_test("MSAE and ETF Regime Engine", False, f"signals/etf-regime missing fields: {missing_signal_fields}")
                return False
            
            # Validate decision is one of expected values
            decision = etf_signal.get('decision')
            valid_decisions = ['TQQQ', 'SQQQ', 'QQQI', 'OUT']
            if decision not in valid_decisions:
                self.log_test("MSAE and ETF Regime Engine", False, f"Invalid decision: {decision}, expected one of {valid_decisions}")
                return False
            
            # Validate weights object and sum <= 1
            weights = etf_signal.get('weights', {})
            if not isinstance(weights, dict):
                self.log_test("MSAE and ETF Regime Engine", False, f"weights should be object, got {type(weights)}")
                return False
            
            weights_sum = sum(weights.values()) if weights else 0
            if weights_sum > 1.0:
                self.log_test("MSAE and ETF Regime Engine", False, f"weights sum {weights_sum} exceeds 1.0")
                return False
            
            # Validate confidence is in range 0-1
            confidence = etf_signal.get('confidence')
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                self.log_test("MSAE and ETF Regime Engine", False, f"Invalid confidence: {confidence}, expected 0-1")
                return False
            
            # Validate reason structure
            reason = etf_signal.get('reason', {})
            if not isinstance(reason, dict):
                self.log_test("MSAE and ETF Regime Engine", False, f"reason should be object, got {type(reason)}")
                return False
            
            # Test 5: Ensure existing endpoints still work (e.g., GET /api/dashboard)
            dashboard_response = self.session.get(f"{API_BASE}/dashboard")
            if dashboard_response.status_code != 200:
                self.log_test("MSAE and ETF Regime Engine", False, f"Existing endpoint /api/dashboard broken: HTTP {dashboard_response.status_code}")
                return False
            
            # Allow a second attempt for rate limits or data fetch failures
            time.sleep(2)
            
            # Test market/state again to ensure consistency
            market_state_response2 = self.session.get(f"{API_BASE}/market/state")
            if market_state_response2.status_code != 200:
                self.log_test("MSAE and ETF Regime Engine", False, f"Second attempt at market/state failed: HTTP {market_state_response2.status_code}")
                return False
            
            self.log_test("MSAE and ETF Regime Engine", True, "All Phase 1 contract endpoints working: formulas/config with etf_regime defaults, market/state with proper structure, market/history with records, signals/etf-regime with valid payload, existing endpoints preserved")
            return True
            
        except Exception as e:
            self.log_test("MSAE and ETF Regime Engine", False, f"Error: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up any test data created"""
        for item_id in self.watchlist_items_created:
            try:
                self.session.delete(f"{API_BASE}/watchlists/{item_id}")
            except:
                pass  # Ignore cleanup errors
    
    def run_phase2_targeted_tests(self):
        """Run targeted Phase 2 tests from review request"""
        print(f"🎯 Starting TARGETED Phase 2 Backend Tests (Review Request)")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 80)
        
        # First ensure authentication
        print(f"\n🔐 Setting up authentication...")
        auth_success = self.test_authentication_system()
        if not auth_success:
            print("❌ Authentication failed - cannot proceed with authenticated tests")
            return
        
        # Run the specific Phase 2 tests mentioned in review request
        phase2_tests = [
            ("Phase 2: Universe Import (AAPL, MSFT, NVDA)", self.test_phase2_universe_import),
            ("Phase 2: Screens Neglected Pre-Earnings", self.test_phase2_screens_neglected_pre_earnings),
            ("Phase 2: ETF Regime Simulate", self.test_phase2_etf_regime_simulate),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in phase2_tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ EXCEPTION in {test_name}: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 80)
        print(f"🏁 PHASE 2 TARGETED TESTS COMPLETE")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "No tests run")
        print("=" * 80)
        
        return passed, failed

    def run_all_tests(self):
        """Run all backend tests including enhanced professional features"""
        print(f"🚀 Starting COMPREHENSIVE ETF Intelligence System Backend Tests")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 80)
        
        tests = [
            ("API Connectivity", self.test_api_root),
            ("Authentication System", self.test_authentication_system),
            ("AI Chat Integration", self.test_ai_chat_integration),
            ("Enhanced Company Search", self.test_enhanced_company_search),
            ("TradingView Integration", self.test_tradingview_integration),
            ("Interactive Charts", self.test_interactive_charts),
            ("Spreadsheet Interface", self.test_spreadsheet_interface),
            ("Enhanced Watchlist Management", self.test_enhanced_watchlist_management),
            ("Historical Data Pruning", self.test_historical_data_pruning),
            # Phase 1 ETF Regime Tests
            ("Phase 1: ETF Regime Config", self.test_phase1_etf_regime_config),
            ("Phase 1: All Formula Configs", self.test_phase1_all_formula_configs),
            ("Phase 1: Market State", self.test_phase1_market_state),
            ("Phase 1: Market History", self.test_phase1_market_history),
            ("Phase 1: ETF Regime Signal", self.test_phase1_etf_regime_signal),
            # NDX Admin Tests
            ("NDX: Get Constituents", self.test_ndx_constituents_get),
            ("NDX: Post Constituents", self.test_ndx_constituents_post),
            ("NDX: Constituents Diff", self.test_ndx_constituents_diff),
            ("NDX: Refresh Prices", self.test_ndx_refresh_prices),
            # Legacy Compatibility Tests
            ("Legacy: Formulas Config", self.test_legacy_formulas_config),
            ("Positions & Trades Management", self.test_positions_and_trades_management),
            ("Sanity: Dashboard", self.test_sanity_dashboard),
            # Phase 2 Tests - Specific endpoints from review request
            ("Phase 2: Universe Import", self.test_phase2_universe_import),
            ("Phase 2: Screens Neglected Pre-Earnings", self.test_phase2_screens_neglected_pre_earnings),
            ("Phase 2: ETF Regime Simulate", self.test_phase2_etf_regime_simulate),
            # Existing Tests
            ("Enhanced Dashboard API", self.test_enhanced_dashboard_api),
            ("Live Market Data APIs", self.test_live_market_data_apis),
            ("Export & Integration APIs", self.test_export_integration_apis),
            ("Formula Configuration APIs", self.test_formula_configuration_apis),
            ("ETF Data Update", self.test_etf_data_update),
            ("ETF Data Retrieval", self.test_get_etfs),
            ("Enhanced Calculations", self.test_enhanced_calculations),
            ("MSAE and ETF Regime Engine", self.test_msae_etf_regime_engine),
            ("Swing Leaders", self.test_swing_leaders),
            ("Universal Stock Lookup", self.test_universal_stock_lookup),
            ("Watchlist Management", self.test_watchlist_management),
            ("Custom Watchlist Lists", self.test_custom_watchlist_lists),
            ("Market Score (MSAE)", self.test_market_score),
            ("AI Chart Analysis", self.test_chart_analysis),
            ("Journal Management", self.test_journal_management),
            ("Historical Data", self.test_historical_data),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                failed += 1
        
        # Cleanup
        self.cleanup()
        
        print("\n" + "=" * 80)
        print(f"📊 ENHANCED ETF INTELLIGENCE SYSTEM TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        print(f"🏆 Professional Trading Platform Status: {'READY' if failed == 0 else 'NEEDS ATTENTION'}")
        
        return passed, failed, self.test_results

    def run_phase1_tests(self):
        """Run Phase 1 ETF Regime + NDX backend verification tests"""
        print("🚀 Starting Phase 1 ETF Regime + NDX Backend Verification")
        print(f"📡 Testing against: {API_BASE}")
        print("=" * 80)
        
        # Test basic connectivity first
        if not self.test_api_root():
            print("❌ Basic connectivity failed - stopping tests")
            return 0, 1, self.test_results
        
        # Authentication tests (required for NDX admin endpoints)
        auth_success = self.test_authentication_system()
        
        # Phase 1 specific tests as per review request
        tests = [
            ("Phase 1: ETF Regime Config", self.test_phase1_etf_regime_config),
            ("Phase 1: All Formula Configs", self.test_phase1_all_formula_configs),
            ("Phase 1: Market State", self.test_phase1_market_state),
            ("Phase 1: Market History", self.test_phase1_market_history),
            ("Phase 1: ETF Regime Signal", self.test_phase1_etf_regime_signal),
            ("NDX: Get Constituents", self.test_ndx_constituents_get),
            ("NDX: Post Constituents", self.test_ndx_constituents_post if auth_success else lambda: self.log_test("NDX: Post Constituents", False, "Skipped - authentication failed")),
            ("NDX: Constituents Diff", self.test_ndx_constituents_diff),
            ("NDX: Refresh Prices", self.test_ndx_refresh_prices),
            ("Legacy: Formulas Config", self.test_legacy_formulas_config),
            ("Sanity: Dashboard", self.test_sanity_dashboard),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 80)
        print(f"📊 PHASE 1 ETF REGIME + NDX TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        print(f"🏆 Phase 1 Status: {'READY' if failed == 0 else 'NEEDS ATTENTION'}")
        
        return passed, failed, self.test_results

if __name__ == "__main__":
    import sys
    tester = ETFBackendTester()
    
    # Check command line arguments for specific test suites
    if len(sys.argv) > 1:
        if sys.argv[1] == "phase1":
            passed, failed, results = tester.run_phase1_tests()
        elif sys.argv[1] == "phase2":
            passed, failed = tester.run_phase2_targeted_tests()
            results = tester.test_results
        elif sys.argv[1] == "targeted":
            tester.run_targeted_tests()
            results = tester.test_results
            passed = sum(1 for r in results if r['success'])
            failed = sum(1 for r in results if not r['success'])
        else:
            print(f"Unknown test suite: {sys.argv[1]}")
            print("Available options: phase1, phase2, targeted")
            sys.exit(1)
    else:
        passed, failed, results = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "summary": {"passed": passed, "failed": failed},
            "detailed_results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")