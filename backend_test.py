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