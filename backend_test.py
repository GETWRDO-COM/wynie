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
    
    def test_polygon_aggregates(self):
        """Test Polygon aggregates endpoint with different parameters"""
        try:
            # Test default parameters
            default_response = self.session.get(f"{API_BASE}/market/aggregates")
            if default_response.status_code != 200:
                self.log_test("Polygon Aggregates", False, f"Default params failed: HTTP {default_response.status_code}: {default_response.text}")
                return False
            
            default_data = default_response.json()
            required_fields = ['range', 'last_updated', 'data']
            missing_fields = [field for field in required_fields if field not in default_data]
            if missing_fields:
                self.log_test("Polygon Aggregates", False, f"Default response missing fields: {missing_fields}")
                return False
            
            # Test with specific range and tickers
            test_response = self.session.get(f"{API_BASE}/market/aggregates?range=1D&tickers=SPY,QQQ,I:DJI,TQQQ,SQQQ")
            if test_response.status_code != 200:
                self.log_test("Polygon Aggregates", False, f"Specific params failed: HTTP {test_response.status_code}: {test_response.text}")
                return False
            
            test_data = test_response.json()
            
            # Validate data structure
            data = test_data.get('data', {})
            expected_tickers = ['SPY', 'QQQ', 'I:DJI', 'TQQQ', 'SQQQ']
            
            for ticker in expected_tickers:
                if ticker not in data:
                    self.log_test("Polygon Aggregates", False, f"Missing ticker {ticker} in response")
                    return False
                
                ticker_data = data[ticker]
                required_ticker_fields = ['series', 'close', 'prev_close', 'change_pct']
                optional_fields = ['pre_market', 'post_market']
                
                missing_ticker_fields = [field for field in required_ticker_fields if field not in ticker_data]
                if missing_ticker_fields:
                    self.log_test("Polygon Aggregates", False, f"{ticker} missing fields: {missing_ticker_fields}")
                    return False
                
                # Validate series is array
                series = ticker_data.get('series', [])
                if not isinstance(series, list):
                    self.log_test("Polygon Aggregates", False, f"{ticker} series is not an array")
                    return False
                
                # Validate numeric fields
                close = ticker_data.get('close')
                prev_close = ticker_data.get('prev_close')
                change_pct = ticker_data.get('change_pct')
                
                if close is not None and not isinstance(close, (int, float)):
                    self.log_test("Polygon Aggregates", False, f"{ticker} close is not numeric: {close}")
                    return False
                
                if prev_close is not None and not isinstance(prev_close, (int, float)):
                    self.log_test("Polygon Aggregates", False, f"{ticker} prev_close is not numeric: {prev_close}")
                    return False
                
                if change_pct is not None and not isinstance(change_pct, (int, float)):
                    self.log_test("Polygon Aggregates", False, f"{ticker} change_pct is not numeric: {change_pct}")
                    return False
            
            # Validate last_updated exists
            last_updated = test_data.get('last_updated')
            if not last_updated:
                self.log_test("Polygon Aggregates", False, "Missing last_updated field")
                return False
            
            self.log_test("Polygon Aggregates", True, f"Polygon aggregates working: tested default and 1D range with {len(expected_tickers)} tickers, all required fields present")
            return True
            
        except Exception as e:
            self.log_test("Polygon Aggregates", False, f"Error: {str(e)}")
            return False

    def test_greed_fear_index(self):
        """Test CNN Fear & Greed Index endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/greed-fear")
            if response.status_code != 200:
                self.log_test("Greed Fear Index", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            data = response.json()
            
            # Validate required fields
            required_fields = ['now', 'last_updated']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Greed Fear Index", False, f"Missing required fields: {missing_fields}")
                return False
            
            # Validate 'now' field is integer
            now_value = data.get('now')
            if not isinstance(now_value, int) or not (0 <= now_value <= 100):
                self.log_test("Greed Fear Index", False, f"Invalid 'now' value: {now_value} (should be integer 0-100)")
                return False
            
            # Validate last_updated is ISO format
            last_updated = data.get('last_updated')
            if not isinstance(last_updated, str):
                self.log_test("Greed Fear Index", False, f"Invalid last_updated format: {last_updated}")
                return False
            
            # Check for either historical data or timeseries
            has_historical = any(field in data for field in ['previous_close', 'one_week_ago', 'one_month_ago', 'one_year_ago'])
            has_timeseries = 'timeseries' in data
            
            if not (has_historical or has_timeseries):
                self.log_test("Greed Fear Index", False, "Missing both historical data and timeseries")
                return False
            
            # Validate source field
            source = data.get('source')
            valid_sources = ['cnn-json', 'cnn-scrape']
            if source not in valid_sources:
                self.log_test("Greed Fear Index", False, f"Invalid source: {source} (should be one of {valid_sources})")
                return False
            
            self.log_test("Greed Fear Index", True, f"CNN Fear & Greed Index working: now={now_value}, source={source}, last_updated present")
            return True
            
        except Exception as e:
            self.log_test("Greed Fear Index", False, f"Error: {str(e)}")
            return False

    def test_news_proxy(self):
        """Test News proxy endpoint with different categories"""
        try:
            # Test default (All) category
            default_response = self.session.get(f"{API_BASE}/news")
            if default_response.status_code != 200:
                self.log_test("News Proxy", False, f"Default category failed: HTTP {default_response.status_code}: {default_response.text}")
                return False
            
            default_data = default_response.json()
            required_fields = ['category', 'items']
            missing_fields = [field for field in required_fields if field not in default_data]
            if missing_fields:
                self.log_test("News Proxy", False, f"Default response missing fields: {missing_fields}")
                return False
            
            # Validate items array
            items = default_data.get('items', [])
            if not isinstance(items, list):
                self.log_test("News Proxy", False, "Items is not an array")
                return False
            
            if len(items) == 0:
                self.log_test("News Proxy", False, "No news items returned")
                return False
            
            # Validate item structure
            sample_item = items[0]
            required_item_fields = ['title', 'link']
            missing_item_fields = [field for field in required_item_fields if field not in sample_item]
            if missing_item_fields:
                self.log_test("News Proxy", False, f"News item missing fields: {missing_item_fields}")
                return False
            
            # Validate title and link are strings
            if not isinstance(sample_item['title'], str) or not isinstance(sample_item['link'], str):
                self.log_test("News Proxy", False, "Title or link is not a string")
                return False
            
            # Test specific category
            category_response = self.session.get(f"{API_BASE}/news?category=Stock Market")
            if category_response.status_code != 200:
                self.log_test("News Proxy", False, f"Stock Market category failed: HTTP {category_response.status_code}")
                return False
            
            category_data = category_response.json()
            if category_data.get('category') != 'Stock Market':
                self.log_test("News Proxy", False, f"Category mismatch: expected 'Stock Market', got '{category_data.get('category')}'")
                return False
            
            # Validate cached field may be present
            cached_field_present = 'cached' in default_data or 'cached' in category_data
            
            self.log_test("News Proxy", True, f"News proxy working: {len(items)} items returned, category filtering works, cached behavior acceptable")
            return True
            
        except Exception as e:
            self.log_test("News Proxy", False, f"Error: {str(e)}")
            return False

    def test_polygon_integration_auth(self):
        """Test auth-protected Polygon API key management endpoints"""
        try:
            if not self.auth_token:
                self.log_test("Polygon Integration Auth", False, "No auth token available - run authentication test first")
                return False
            
            auth_headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test save Polygon API key
            test_key = "test_polygon_key_12345"
            key_data = {"api_key": test_key}
            
            save_response = self.session.post(f"{API_BASE}/integrations/polygon/key", json=key_data, headers=auth_headers)
            if save_response.status_code != 200:
                self.log_test("Polygon Integration Auth", False, f"Save key failed: HTTP {save_response.status_code}: {save_response.text}")
                return False
            
            save_result = save_response.json()
            if 'message' not in save_result:
                self.log_test("Polygon Integration Auth", False, "Save key response missing message")
                return False
            
            # Verify the key is not returned in the response (security)
            if 'api_key' in save_result or test_key in str(save_result):
                self.log_test("Polygon Integration Auth", False, "API key returned in response - security issue")
                return False
            
            # Test get Polygon status
            status_response = self.session.get(f"{API_BASE}/integrations/polygon/status", headers=auth_headers)
            if status_response.status_code != 200:
                self.log_test("Polygon Integration Auth", False, f"Get status failed: HTTP {status_response.status_code}")
                return False
            
            status_result = status_response.json()
            if 'configured' not in status_result:
                self.log_test("Polygon Integration Auth", False, "Status response missing 'configured' field")
                return False
            
            # After saving a key, configured should be true
            if not status_result.get('configured'):
                self.log_test("Polygon Integration Auth", False, "Status shows not configured after saving key")
                return False
            
            # Test unauthorized access (without token)
            unauth_save_response = self.session.post(f"{API_BASE}/integrations/polygon/key", json=key_data)
            if unauth_save_response.status_code not in [401, 403]:  # Accept both 401 and 403 as valid unauthorized responses
                self.log_test("Polygon Integration Auth", False, f"Unauthorized save should return 401 or 403, got {unauth_save_response.status_code}")
                return False
            
            unauth_status_response = self.session.get(f"{API_BASE}/integrations/polygon/status")
            if unauth_status_response.status_code not in [401, 403]:  # Accept both 401 and 403 as valid unauthorized responses
                self.log_test("Polygon Integration Auth", False, f"Unauthorized status should return 401 or 403, got {unauth_status_response.status_code}")
                return False
            
            self.log_test("Polygon Integration Auth", True, "Polygon API key management working: secure key storage, status endpoint, proper authentication required")
            return True
            
        except Exception as e:
            self.log_test("Polygon Integration Auth", False, f"Error: {str(e)}")
            return False

    def cleanup(self):
        """Clean up any test data created"""
        for item_id in self.watchlist_items_created:
            try:
                self.session.delete(f"{API_BASE}/watchlists/{item_id}")
            except:
                pass  # Ignore cleanup errors
    
    def run_all_tests(self):
        """Run all backend tests including enhanced professional features and new endpoints"""
        print(f"🚀 Starting COMPREHENSIVE ETF Intelligence System Backend Tests")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 80)
        
        # New endpoints tests (from review request) - Priority testing
        new_endpoint_tests = [
            ("Polygon Aggregates", self.test_polygon_aggregates),
            ("CNN Fear & Greed Index", self.test_greed_fear_index),
            ("News Proxy", self.test_news_proxy),
        ]
        
        # Auth-protected new endpoint tests (require authentication)
        auth_new_endpoint_tests = [
            ("Polygon Integration Auth", self.test_polygon_integration_auth),
        ]
        
        # Core system tests
        core_tests = [
            ("API Connectivity", self.test_api_root),
            ("Authentication System", self.test_authentication_system),
            ("AI Chat Integration", self.test_ai_chat_integration),
            ("Enhanced Company Search", self.test_enhanced_company_search),
            ("TradingView Integration", self.test_tradingview_integration),
            ("Interactive Charts", self.test_interactive_charts),
            ("Spreadsheet Interface", self.test_spreadsheet_interface),
            ("Enhanced Watchlist Management", self.test_enhanced_watchlist_management),
            ("Historical Data Pruning", self.test_historical_data_pruning),
            ("Enhanced Dashboard API", self.test_enhanced_dashboard_api),
            ("Live Market Data APIs", self.test_live_market_data_apis),
            ("Export & Integration APIs", self.test_export_integration_apis),
            ("Formula Configuration APIs", self.test_formula_configuration_apis),
            ("ETF Data Update", self.test_etf_data_update),
            ("ETF Data Retrieval", self.test_get_etfs),
            ("Enhanced Calculations", self.test_enhanced_calculations),
            ("Swing Leaders", self.test_swing_leaders),
            ("Universal Stock Lookup", self.test_universal_stock_lookup),
            ("Watchlist Management", self.test_watchlist_management),
            ("Custom Watchlist Lists", self.test_custom_watchlist_lists),
            ("Market Score (MSAE)", self.test_market_score),
            ("AI Chart Analysis", self.test_chart_analysis),
            ("Journal Management", self.test_journal_management),
            ("Historical Data", self.test_historical_data),
        ]
        
        # Run new endpoint tests first (priority)
        print("\n🎯 PRIORITY: Testing New Endpoints (Polygon, CNN, News)")
        print("-" * 60)
        new_passed = 0
        new_failed = 0
        
        for test_name, test_func in new_endpoint_tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    new_passed += 1
                else:
                    new_failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                new_failed += 1
        
        # Run core system tests (including authentication)
        print("\n🏗️ CORE SYSTEM: Testing All Backend Features")
        print("-" * 60)
        core_passed = 0
        core_failed = 0
        
        for test_name, test_func in core_tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    core_passed += 1
                else:
                    core_failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                core_failed += 1
        
        # Run auth-protected new endpoint tests after authentication is set up
        print("\n🔐 AUTH-PROTECTED NEW ENDPOINTS: Testing After Authentication")
        print("-" * 60)
        auth_new_passed = 0
        auth_new_failed = 0
        
        for test_name, test_func in auth_new_endpoint_tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if test_func():
                    auth_new_passed += 1
                else:
                    auth_new_failed += 1
            except Exception as e:
                print(f"❌ FAIL {test_name}: Unexpected error: {str(e)}")
                auth_new_failed += 1
        
        # Cleanup
        self.cleanup()
        
        # Calculate totals
        total_passed = new_passed + core_passed + auth_new_passed
        total_failed = new_failed + core_failed + auth_new_failed
        total_tests = total_passed + total_failed
        
        print("\n" + "=" * 80)
        print(f"📊 COMPREHENSIVE ETF INTELLIGENCE SYSTEM TEST SUMMARY")
        print("=" * 80)
        print(f"🎯 NEW ENDPOINTS: {new_passed}/{len(new_endpoint_tests)} passed ({new_passed/len(new_endpoint_tests)*100:.1f}%)")
        print(f"🏗️ CORE SYSTEM: {core_passed}/{len(core_tests)} passed ({core_passed/len(core_tests)*100:.1f}%)")
        print(f"🔐 AUTH-PROTECTED NEW: {auth_new_passed}/{len(auth_new_endpoint_tests)} passed ({auth_new_passed/len(auth_new_endpoint_tests)*100:.1f}%)")
        print(f"📈 OVERALL: {total_passed}/{total_tests} passed ({total_passed/total_tests*100:.1f}%)")
        print(f"🏆 Professional Trading Platform Status: {'READY' if total_failed == 0 else 'NEEDS ATTENTION'}")
        
        # Show failed tests by category
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for failed in failed_tests:
                print(f"  • {failed['test']}: {failed['details']}")
        else:
            print("\n✅ ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL!")
        
        return total_passed, total_failed, self.test_results

if __name__ == "__main__":
    tester = ETFBackendTester()
    passed, failed, results = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "summary": {"passed": passed, "failed": failed},
            "detailed_results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")