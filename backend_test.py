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
            expected_config_sections = ['relative_strength', 'sata_weights', 'atr_calculation', 'gmma_pattern']
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
    
    def cleanup(self):
        """Clean up any test data created"""
        for item_id in self.watchlist_items_created:
            try:
                self.session.delete(f"{API_BASE}/watchlists/{item_id}")
            except:
                pass  # Ignore cleanup errors
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"🚀 Starting ETF Intelligence System Backend Tests")
        print(f"📡 Backend URL: {BACKEND_URL}")
        print(f"🔗 API Base: {API_BASE}")
        print("=" * 60)
        
        tests = [
            ("API Connectivity", self.test_api_root),
            ("Dashboard API", self.test_dashboard_api),
            ("ETF Data Update", self.test_etf_data_update),
            ("ETF Data Retrieval", self.test_get_etfs),
            ("ETF Calculations", self.test_etf_calculations),
            ("Swing Leaders", self.test_swing_leaders),
            ("Universal Stock Lookup", self.test_universal_stock_lookup),
            ("Watchlist Management", self.test_watchlist_management),
            ("Custom Watchlist Lists", self.test_custom_watchlist_lists),
            ("Market Score (MSAE)", self.test_market_score),
            ("Chart Analysis", self.test_chart_analysis),
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
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        return passed, failed, self.test_results

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