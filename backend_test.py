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
            lists_response = self.session.get(f"{API_BASE}/watchlists/lists")
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
                self.log_test("Historical Data", False, f"30 days parameter failed: HTTP {days_response_30.status_code}")
                return False
            
            self.log_test("Historical Data", True, "Historical snapshots endpoint working correctly")
            return True
            
        except Exception as e:
            self.log_test("Historical Data", False, f"Error: {str(e)}")
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
            ("ETF Data Update", self.test_etf_data_update),
            ("ETF Data Retrieval", self.test_get_etfs),
            ("ETF Calculations", self.test_etf_calculations),
            ("ETF Leaders", self.test_etf_leaders),
            ("Watchlist Management", self.test_watchlist_management),
            ("Market Score (MSAE)", self.test_market_score),
            ("Chart Analysis", self.test_chart_analysis),
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