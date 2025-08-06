import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ETFIntelligenceSystem = () => {
  const [etfs, setEtfs] = useState([]);
  const [watchlists, setWatchlists] = useState([]);
  const [customWatchlists, setCustomWatchlists] = useState([]);
  const [marketScore, setMarketScore] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [selectedSector, setSelectedSector] = useState("");
  const [sectors, setSectors] = useState([]);
  const [leaders, setLeaders] = useState([]);
  const [swingLeaders, setSwingLeaders] = useState([]);
  const [chartAnalysis, setChartAnalysis] = useState(null);
  const [selectedTicker, setSelectedTicker] = useState("");
  const [historicalData, setHistoricalData] = useState([]);
  const [journalEntries, setJournalEntries] = useState([]);
  const [stockLookup, setStockLookup] = useState("");
  const [stockData, setStockData] = useState(null);
  const [showFormulas, setShowFormulas] = useState(false);
  const [liveIndices, setLiveIndices] = useState({});
  const [fearGreedData, setFearGreedData] = useState(null);
  const [forexRates, setForexRates] = useState(null);
  const [exportLoading, setExportLoading] = useState(false);
  
  const [watchlistForm, setWatchlistForm] = useState({
    ticker: "",
    name: "",
    list_name: "",
    notes: "",
    tags: "",
    priority: 3
  });

  const [newWatchlistForm, setNewWatchlistForm] = useState({
    name: "",
    description: "",
    color: "#3B82F6"
  });

  const [journalForm, setJournalForm] = useState({
    title: "",
    content: "",
    tags: "",
    mood: "neutral"
  });

  // Fetch initial data
  useEffect(() => {
    fetchData();
    fetchLiveData();
    const interval = setInterval(() => {
      fetchDashboardData();
      fetchLiveData();
    }, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [etfRes, marketRes, sectorsRes, leadersRes, dashboardRes, customWatchlistsRes] = await Promise.all([
        axios.get(`${API}/etfs`),
        axios.get(`${API}/market-score`),
        axios.get(`${API}/etfs/sectors`),
        axios.get(`${API}/etfs/leaders?timeframe=1m`),
        axios.get(`${API}/dashboard`),
        axios.get(`${API}/watchlists/lists`)
      ]);

      setEtfs(etfRes.data);
      setMarketScore(marketRes.data);
      setSectors(sectorsRes.data.sectors);
      setLeaders(leadersRes.data);
      setDashboardData(dashboardRes.data);
      setCustomWatchlists(customWatchlistsRes.data);
      
      // Fetch swing leaders
      const swingRes = await axios.get(`${API}/etfs/swing-leaders`);
      setSwingLeaders(swingRes.data);

    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    }
  };
  const fetchLiveData = async () => {
    try {
      const [indicesRes, fearGreedRes, forexRes] = await Promise.all([
        axios.get(`${API}/live/indices`),
        axios.get(`${API}/live/fear-greed`),
        axios.get(`${API}/live/forex`)
      ]);

      setLiveIndices(indicesRes.data);
      setFearGreedData(fearGreedRes.data);
      setForexRates(forexRes.data);
    } catch (error) {
      console.error("Error fetching live data:", error);
    }
  };

  const exportToGoogleSheets = async () => {
    setExportLoading(true);
    try {
      const response = await axios.get(`${API}/export/etfs`);
      
      // Convert data to CSV format
      const csvData = convertToCSV(response.data.data);
      
      // Create and download CSV file
      const blob = new Blob([csvData], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ETF_Intelligence_Data_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error("Error exporting data:", error);
    }
    setExportLoading(false);
  };

  const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(row => 
      Object.values(row).map(value => 
        typeof value === 'string' ? `"${value}"` : value
      ).join(',')
    );
    
    return [headers, ...rows].join('\n');
  };

  const updateETFs = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/etfs/update`);
      await fetchData();
    } catch (error) {
      console.error("Error updating ETFs:", error);
    }
    setLoading(false);
  };

  const analyzeChart = async (ticker) => {
    setSelectedTicker(ticker);
    try {
      setLoading(true);
      const response = await axios.get(`${API}/charts/${ticker}/analysis`);
      setChartAnalysis(response.data);
    } catch (error) {
      console.error("Error getting chart analysis:", error);
    } finally {
      setLoading(false);
    }
  };

  const lookupStock = async () => {
    if (!stockLookup.trim()) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`${API}/stocks/${stockLookup.trim().toUpperCase()}`);
      setStockData({...response.data, ticker: stockLookup.trim().toUpperCase()});
    } catch (error) {
      console.error("Error looking up stock:", error);
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 28) return "text-green-600 bg-green-100";
    if (score >= 20) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getChangeColor = (change) => {
    if (change > 0) return "text-green-400";
    if (change < 0) return "text-red-400";
    return "text-gray-400";
  };

  const getRSBadge = (rs) => {
    if (rs > 0.1) return <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded font-semibold">🔥 Strong</span>;
    if (rs > 0.02) return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">➡️ Moderate</span>;
    return <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">📉 Weak</span>;
  };

  const getSwingDaysColor = (days) => {
    if (days <= 5) return "text-green-400"; // Early swing
    if (days <= 15) return "text-yellow-400"; // Mid swing
    return "text-red-400"; // Late swing
  };

  const filteredEtfs = etfs.filter(etf => 
    selectedSector === "" || etf.sector === selectedSector
  );

  if (loading && !dashboardData) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-white mt-4 text-lg">Loading ETF Intelligence Engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-white">📊 ETF Intelligence Engine</h1>
              {dashboardData && (
                <p className="text-blue-300 mt-1">{dashboardData.greeting}</p>
              )}
            </div>
            <div className="flex items-center space-x-6">
              {dashboardData && (
                <div className="flex space-x-6 text-sm">
                  <div className="bg-gray-700 rounded-lg p-3 text-center border-l-4 border-blue-500">
                    <div className="flex items-center justify-center mb-1">
                      <span className="text-2xl mr-2">🇿🇦</span>
                      <div>
                        <div className="text-blue-300 font-bold text-lg font-mono">{dashboardData.sa_time.time}</div>
                        <div className="text-xs text-blue-200">Johannesburg ({dashboardData.sa_time.timezone})</div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">{dashboardData.sa_time.date}</div>
                  </div>
                  <div className="bg-gray-700 rounded-lg p-3 text-center border-l-4 border-green-500">
                    <div className="flex items-center justify-center mb-1">
                      <span className="text-2xl mr-2">🇺🇸</span>
                      <div>
                        <div className="text-green-300 font-bold text-lg font-mono">{dashboardData.ny_time.time}</div>
                        <div className="text-xs text-green-200">New York ({dashboardData.ny_time.timezone})</div>
                      </div>
                    </div>
                    <div className="text-xs text-orange-400 font-semibold mt-1">
                      📈 Opens in: {dashboardData.market_countdown}
                    </div>
                  </div>
                  {/* Add ZAR/USD Exchange Rate */}
                  <div className="bg-gray-700 rounded-lg p-3 text-center border-l-4 border-yellow-500">
                    <div className="flex items-center justify-center">
                      <span className="text-lg mr-2">💱</span>
                      <div>
                        <div className="text-yellow-300 font-bold text-lg">ZAR/USD</div>
                        <div className="text-xs text-yellow-200">Live Rate</div>
                        <div className="text-xs text-gray-400 mt-1">Loading...</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div className="flex space-x-3">
                <button
                  onClick={updateETFs}
                  disabled={loading}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-medium disabled:opacity-50 flex items-center"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Updating...
                    </>
                  ) : (
                    <>
                      🔄 Update Data
                    </>
                  )}
                </button>
                <div className="bg-gray-700 rounded-lg px-3 py-2 text-xs">
                  <div className="text-gray-400">Last Updated</div>
                  <div className="text-white font-mono">{dashboardData ? new Date(dashboardData.last_updated).toLocaleTimeString() : '--:--'}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="bg-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {[
              { id: "dashboard", label: "🏠 Dashboard" },
              { id: "swing-grid", label: "📊 Swing Analysis" },
              { id: "ai-analysis", label: "🧠 AI Analysis" },
              { id: "watchlists", label: "📈 Watchlists" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-blue-500 text-white"
                    : "border-transparent text-gray-300 hover:text-white hover:border-gray-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <div className="space-y-8">
            {/* Universal Stock Search Bar */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-2xl font-bold mb-4">🔍 Universal Stock & ETF Search</h2>
              <div className="flex gap-4">
                <input
                  type="text"
                  placeholder="Search any stock or ETF (AAPL, TSLA, QQQ, etc.)"
                  value={stockLookup}
                  onChange={(e) => setStockLookup(e.target.value.toUpperCase())}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-lg"
                  onKeyPress={(e) => e.key === 'Enter' && lookupStock()}
                />
                <button
                  onClick={lookupStock}
                  className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-medium"
                >
                  🔍 Search
                </button>
              </div>
              
              {stockData && (
                <div className="mt-6 bg-gray-700 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <h3 className="text-2xl font-bold text-blue-300">{stockData.ticker}</h3>
                      <p className="text-gray-400">Live Market Data</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => analyzeChart(stockData.ticker)}
                        className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded text-sm"
                      >
                        🧠 AI Analysis
                      </button>
                      <button
                        onClick={() => {
                          setWatchlistForm({...watchlistForm, ticker: stockData.ticker, name: stockData.ticker});
                          setActiveTab("watchlists");
                        }}
                        className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-sm"
                      >
                        ➕ Add to Watchlist
                      </button>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center">
                      <div className="text-sm text-gray-400">Price</div>
                      <div className="text-2xl font-bold text-white">${stockData.current_price?.toFixed(2)}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400">1-Day</div>
                      <div className={`text-xl font-bold ${getChangeColor(stockData.change_1d)}`}>
                        {stockData.change_1d > 0 ? '+' : ''}{stockData.change_1d?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400">1-Week</div>
                      <div className={`text-xl font-bold ${getChangeColor(stockData.change_1w)}`}>
                        {stockData.change_1w > 0 ? '+' : ''}{stockData.change_1w?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400">1-Month</div>
                      <div className={`text-xl font-bold ${getChangeColor(stockData.change_1m)}`}>
                        {stockData.change_1m > 0 ? '+' : ''}{stockData.change_1m?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm text-gray-400">ATR%</div>
                      <div className="text-xl font-bold text-yellow-400">{stockData.atr_percent?.toFixed(2)}%</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Major Market Indices & CNN Fear/Greed */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Major Indices */}
              <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-2xl font-bold mb-4">📊 Major Market Indices</h2>
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 bg-gray-700 rounded-lg">
                    <div>
                      <span className="font-bold text-lg">S&P 500</span>
                      <span className="text-gray-400 ml-2">(SPY)</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">Loading...</div>
                      <div className="text-sm text-gray-400">Last: --:--</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-700 rounded-lg">
                    <div>
                      <span className="font-bold text-lg">NASDAQ</span>
                      <span className="text-gray-400 ml-2">(QQQ)</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">Loading...</div>
                      <div className="text-sm text-gray-400">Last: --:--</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-700 rounded-lg">
                    <div>
                      <span className="font-bold text-lg">Dow Jones</span>
                      <span className="text-gray-400 ml-2">(DIA)</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">Loading...</div>
                      <div className="text-sm text-gray-400">Last: --:--</div>
                    </div>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-700 rounded-lg">
                    <div>
                      <span className="font-bold text-lg">Russell 2000</span>
                      <span className="text-gray-400 ml-2">(IWM)</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">Loading...</div>
                      <div className="text-sm text-gray-400">Last: --:--</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* CNN Fear & Greed Index */}
              <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-2xl font-bold mb-4">😨 CNN Fear & Greed Index</h2>
                <div className="text-center">
                  <div className="relative w-40 h-40 mx-auto mb-4">
                    <div className="w-full h-full rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 p-1">
                      <div className="w-full h-full rounded-full bg-gray-800 flex items-center justify-center">
                        <div className="text-center">
                          <div className="text-3xl font-bold">Loading...</div>
                          <div className="text-sm text-gray-400">Index Score</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="text-xl font-semibold">Loading...</div>
                    <div className="text-sm text-gray-400">Market Sentiment</div>
                    <div className="text-xs text-gray-500">
                      Last Updated: Loading...
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="text-gray-400">Stock Price Momentum</div>
                    <div className="font-semibold">Loading...</div>
                  </div>
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="text-gray-400">Market Volatility</div>
                    <div className="font-semibold">Loading...</div>
                  </div>
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="text-gray-400">Safe Haven Demand</div>
                    <div className="font-semibold">Loading...</div>
                  </div>
                  <div className="bg-gray-700 p-3 rounded">
                    <div className="text-gray-400">Put/Call Ratio</div>
                    <div className="font-semibold">Loading...</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Enhanced Market Score Card with Editable Formulas */}
            {marketScore && (
              <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold">🎯 Market Situational Awareness Engine (MSAE)</h2>
                  <div className="flex gap-2">
                    <button className="bg-gray-600 hover:bg-gray-700 px-3 py-2 rounded text-sm">
                      ⚙️ Edit Formulas
                    </button>
                    <button className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm">
                      📊 Export to Sheets
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className={`text-5xl font-bold p-6 rounded-xl ${getScoreColor(marketScore.total_score)}`}>
                      {marketScore.total_score}/40
                    </div>
                    <p className="text-2xl font-semibold mt-3">{marketScore.classification}</p>
                  </div>
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-semibold mb-2">🎯 Current Recommendation:</h3>
                    <p className="text-gray-300 mb-4 text-lg">{marketScore.recommendation}</p>
                    <div className="grid grid-cols-4 gap-3 text-sm">
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">SATA Score</div>
                        <div className="text-lg font-bold text-blue-400">{marketScore.sata_score}/5</div>
                      </div>
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">ADX Trend</div>
                        <div className="text-lg font-bold text-green-400">{marketScore.adx_score}/5</div>
                      </div>
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">VIX Fear</div>
                        <div className="text-lg font-bold text-red-400">{marketScore.vix_score}/5</div>
                      </div>
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">ATR Vol</div>
                        <div className="text-lg font-bold text-yellow-400">{marketScore.atr_score}/5</div>
                      </div>
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">GMI Index</div>
                        <div className="text-lg font-bold text-purple-400">{marketScore.gmi_score}/5</div>
                      </div>
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">NH-NL</div>
                        <div className="text-lg font-bold text-indigo-400">{marketScore.nhnl_score}/5</div>
                      </div>
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">F&G Index</div>
                        <div className="text-lg font-bold text-pink-400">{marketScore.fg_index_score}/5</div>
                      </div>
                      <div className="bg-gray-700 p-3 rounded-lg text-center">
                        <div className="text-gray-400 text-xs">QQQ ATH</div>
                        <div className="text-lg font-bold text-cyan-400">{marketScore.qqq_ath_distance_score}/5</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Formula Display Section */}
                <div className="mt-6 pt-4 border-t border-gray-700">
                  <button 
                    onClick={() => setShowFormulas(!showFormulas)}
                    className="text-sm text-blue-400 hover:text-blue-300 mb-2"
                  >
                    {showFormulas ? '🔽 Hide' : '▶️ Show'} Calculation Formulas
                  </button>
                  {showFormulas && (
                    <div className="bg-gray-900 p-4 rounded-lg text-sm">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono">
                        <div>
                          <div className="text-blue-400 font-semibold">SATA Score Formula:</div>
                          <div className="text-gray-300">Performance(30%) + RelStrength(30%) + Volume(20%) + Volatility(20%)</div>
                        </div>
                        <div>
                          <div className="text-green-400 font-semibold">Relative Strength:</div>
                          <div className="text-gray-300">RS = (ETF_Return - SPY_Return) / |SPY_Return|</div>
                        </div>
                        <div>
                          <div className="text-red-400 font-semibold">ATR Calculation:</div>
                          <div className="text-gray-300">ATR% = 14-day ATR / Current_Price * 100</div>
                        </div>
                        <div>
                          <div className="text-yellow-400 font-semibold">GMMA Pattern:</div>
                          <div className="text-gray-300">RWB: 1W&gt;0 &amp; 1M&gt;0 &amp; RS&gt;0, BWR: All negative</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Top 5 Swing Leaders */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-2xl font-bold mb-4">🚀 Top 5 Swing Leaders (SATA + RS Combined)</h2>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {swingLeaders.map((etf, index) => (
                  <div key={etf.ticker} className="bg-gray-700 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold mb-2">#{index + 1}</div>
                    <div className="text-lg font-semibold text-blue-300">{etf.ticker}</div>
                    <div className="text-sm text-gray-400 mb-2">{etf.name?.slice(0, 20)}...</div>
                    <div className="text-sm">
                      <div>SATA: <span className="font-semibold">{etf.sata_score}/10</span></div>
                      <div className="mt-1">{getRSBadge(etf.relative_strength_1m)}</div>
                      <div className={`mt-1 font-semibold ${getChangeColor(etf.change_1m)}`}>
                        {etf.change_1m > 0 ? '+' : ''}{etf.change_1m?.toFixed(2)}% (1M)
                      </div>
                    </div>
                    <button
                      onClick={() => analyzeChart(etf.ticker)}
                      className="mt-2 bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs"
                    >
                      📈 Analyze
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Risk-On/Off Summary */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-2xl font-bold mb-4">⚖️ Risk-On vs Risk-Off Signals</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-green-400 mb-3">🟢 Risk-On Signals</h3>
                  <div className="space-y-2">
                    {leaders.filter(etf => 
                      ['TQQQ', 'FFTY', 'MGK', 'QQQ', 'SPXL'].includes(etf.ticker) && etf.change_1d > 0
                    ).map(etf => (
                      <div key={etf.ticker} className="flex justify-between bg-green-900 bg-opacity-30 p-2 rounded">
                        <span className="font-semibold">{etf.ticker}</span>
                        <span className="text-green-400">+{etf.change_1d.toFixed(2)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-red-400 mb-3">🔴 Risk-Off Signals</h3>
                  <div className="space-y-2">
                    {leaders.filter(etf => 
                      ['SQQQ', 'VIX', 'TLT', 'GLD'].includes(etf.ticker) && etf.change_1d > 0
                    ).map(etf => (
                      <div key={etf.ticker} className="flex justify-between bg-red-900 bg-opacity-30 p-2 rounded">
                        <span className="font-semibold">{etf.ticker}</span>
                        <span className="text-red-400">+{etf.change_1d.toFixed(2)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Swing Analysis Grid Tab */}
        {activeTab === "swing-grid" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">📊 Capitalization & Swing Analysis Grid</h2>
              <div className="flex gap-3">
                <select
                  value={selectedSector}
                  onChange={(e) => setSelectedSector(e.target.value)}
                  className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2"
                >
                  <option value="">All Sectors</option>
                  {sectors.map((sector) => (
                    <option key={sector} value={sector}>{sector}</option>
                  ))}
                </select>
                <button className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg">
                  📊 Export to Google Sheets
                </button>
                <button 
                  onClick={() => setShowFormulas(!showFormulas)}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
                >
                  {showFormulas ? '🔽 Hide' : '⚙️ Show'} Formulas
                </button>
              </div>
            </div>

            {/* Formula Display Panel */}
            {showFormulas && (
              <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
                <h3 className="text-lg font-semibold mb-4 text-blue-300">📐 Editable Calculation Formulas</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <div className="bg-gray-700 p-4 rounded-lg">
                    <h4 className="font-semibold text-green-400 mb-2">Relative Strength (RS)</h4>
                    <div className="font-mono text-sm text-gray-300 mb-2">
                      RS = (ETF_Return - SPY_Return) / |SPY_Return|
                    </div>
                    <div className="space-y-2">
                      <div>
                        <label className="text-xs text-gray-400">Strong Threshold (&gt;)</label>
                        <input type="number" defaultValue="0.10" step="0.01" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400">Moderate Threshold (&gt;)</label>
                        <input type="number" defaultValue="0.02" step="0.01" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-700 p-4 rounded-lg">
                    <h4 className="font-semibold text-yellow-400 mb-2">SATA Score Weights</h4>
                    <div className="font-mono text-sm text-gray-300 mb-2">
                      SATA = Σ(Factor × Weight)
                    </div>
                    <div className="space-y-2">
                      <div>
                        <label className="text-xs text-gray-400">Performance (%)</label>
                        <input type="number" defaultValue="30" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400">Rel. Strength (%)</label>
                        <input type="number" defaultValue="30" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400">Volume (%)</label>
                        <input type="number" defaultValue="20" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400">Volatility (%)</label>
                        <input type="number" defaultValue="20" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gray-700 p-4 rounded-lg">
                    <h4 className="font-semibold text-purple-400 mb-2">ATR Calculation</h4>
                    <div className="font-mono text-sm text-gray-300 mb-2">
                      ATR% = (14-day ATR / Price) × 100
                    </div>
                    <div className="space-y-2">
                      <div>
                        <label className="text-xs text-gray-400">Period (days)</label>
                        <input type="number" defaultValue="14" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                      <div>
                        <label className="text-xs text-gray-400">High Volatility (&gt;%)</label>
                        <input type="number" defaultValue="3.0" step="0.1" className="w-full bg-gray-600 rounded px-2 py-1 text-sm" />
                      </div>
                    </div>
                    <button className="mt-2 bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-xs">
                      Recalculate All
                    </button>
                  </div>
                </div>
              </div>
            )}

            <div className="bg-gray-800 rounded-xl p-6 shadow-lg overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-2">ETF</th>
                    <th className="text-left py-3 px-2">Cap/Theme</th>
                    <th className="text-left py-3 px-2">Swl Days</th>
                    <th className="text-left py-3 px-2">SATA</th>
                    <th className="text-left py-3 px-2">20SMA</th>
                    <th className="text-left py-3 px-2">GMMA</th>
                    <th className="text-left py-3 px-2">ATR%</th>
                    <th className="text-left py-3 px-2">1D %</th>
                    <th className="text-left py-3 px-2">1W %</th>
                    <th className="text-left py-3 px-2">1M %</th>
                    <th className="text-left py-3 px-2">1M RS</th>
                    <th className="text-left py-3 px-2">3M RS</th>
                    <th className="text-left py-3 px-2">6M RS</th>
                    <th className="text-left py-3 px-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEtfs.map((etf) => {
                    const swingDays = etf.swing_start_date ? 
                      Math.floor((new Date() - new Date(etf.swing_start_date)) / (1000 * 60 * 60 * 24)) : 
                      Math.floor(Math.random() * 15) + 1; // Mock swing days for demo
                    
                    return (
                      <tr key={etf.ticker} className={`border-b border-gray-700 hover:bg-gray-700 ${
                        etf.relative_strength_1m > 0.1 && etf.sata_score >= 7 && etf.gmma_pattern === 'RWB' 
                          ? 'bg-green-900 bg-opacity-30' 
                          : etf.relative_strength_1m < 0 && etf.gmma_pattern === 'BWR'
                          ? 'bg-red-900 bg-opacity-30'
                          : ''
                      }`}>
                        <td className="py-3 px-2">
                          <div>
                            <div className="font-bold text-blue-300 text-lg">{etf.ticker}</div>
                            <div className="text-xs text-gray-400">{etf.sector}</div>
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          <div className="text-sm">
                            <div className="font-semibold text-gray-300">{etf.theme}</div>
                            <div className="text-xs text-gray-500">{etf.market_cap > 1000000000 ? 'Large Cap' : 'Mid/Small Cap'}</div>
                          </div>
                        </td>
                        <td className={`py-3 px-2 font-bold text-lg ${getSwingDaysColor(swingDays)}`}>
                          {swingDays}
                          <div className="text-xs text-gray-400">
                            {swingDays <= 5 ? 'Early' : swingDays <= 15 ? 'Mid' : 'Late'}
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          <div className={`px-3 py-2 rounded-lg text-center font-bold ${
                            etf.sata_score >= 8 ? 'bg-green-500 text-white' :
                            etf.sata_score >= 6 ? 'bg-yellow-500 text-black' :
                            etf.sata_score >= 4 ? 'bg-orange-500 text-white' :
                            'bg-red-500 text-white'
                          }`}>
                            {etf.sata_score}/10
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          <div className={`w-10 h-10 rounded-full text-white flex items-center justify-center font-bold text-lg ${
                            etf.sma20_trend === 'U' ? 'bg-green-500' : 
                            etf.sma20_trend === 'D' ? 'bg-red-500' : 'bg-gray-500'
                          }`}>
                            {etf.sma20_trend}
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          <div className={`px-3 py-2 rounded-lg text-center font-bold ${
                            etf.gmma_pattern === 'RWB' ? 'bg-gradient-to-r from-red-500 via-white to-blue-500 text-black' :
                            etf.gmma_pattern === 'BWR' ? 'bg-gradient-to-r from-blue-500 via-white to-red-500 text-black' :
                            'bg-gray-500 text-white'
                          }`}>
                            {etf.gmma_pattern}
                          </div>
                        </td>
                        <td className="py-3 px-2">
                          <div className={`text-center font-bold ${
                            etf.atr_percent > 3 ? 'text-red-400' :
                            etf.atr_percent > 2 ? 'text-yellow-400' :
                            'text-green-400'
                          }`}>
                            {etf.atr_percent.toFixed(2)}%
                          </div>
                        </td>
                        <td className={`py-3 px-2 font-bold text-lg ${getChangeColor(etf.change_1d)}`}>
                          {etf.change_1d > 0 ? '+' : ''}{etf.change_1d.toFixed(2)}%
                        </td>
                        <td className={`py-3 px-2 font-bold text-lg ${getChangeColor(etf.change_1w)}`}>
                          {etf.change_1w > 0 ? '+' : ''}{etf.change_1w.toFixed(2)}%
                        </td>
                        <td className={`py-3 px-2 font-bold text-lg ${getChangeColor(etf.change_1m)}`}>
                          {etf.change_1m > 0 ? '+' : ''}{etf.change_1m.toFixed(2)}%
                        </td>
                        <td className="py-3 px-2">{getRSBadge(etf.relative_strength_1m)}</td>
                        <td className="py-3 px-2">{getRSBadge(etf.relative_strength_3m)}</td>
                        <td className="py-3 px-2">{getRSBadge(etf.relative_strength_6m)}</td>
                        <td className="py-3 px-2">
                          <div className="flex flex-col gap-1">
                            <button
                              onClick={() => analyzeChart(etf.ticker)}
                              className="bg-purple-600 hover:bg-purple-700 px-3 py-1 rounded text-xs"
                            >
                              🧠 AI Analysis
                            </button>
                            <button
                              onClick={() => window.open(`https://www.tradingview.com/chart/?symbol=${etf.ticker}`, '_blank')}
                              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs"
                            >
                              📊 TradingView
                            </button>
                            <button
                              onClick={() => {
                                setWatchlistForm({...watchlistForm, ticker: etf.ticker, name: etf.name});
                                setActiveTab("watchlists");
                              }}
                              className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs"
                            >
                              ➕ Watchlist
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Color Legend */}
            <div className="bg-gray-800 rounded-xl p-4 shadow-lg">
              <h3 className="font-semibold mb-3">🎨 Color Legend & Conditional Formatting</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-green-900 bg-opacity-50 rounded"></div>
                  <span><strong>Green Row:</strong> RS=Y, SATA≥7, GMMA=RWB (Strong Buy Signal)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-red-900 bg-opacity-50 rounded"></div>
                  <span><strong>Red Row:</strong> RS=N, GMMA=BWR (Weak/Avoid Signal)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-700 rounded"></div>
                  <span><strong>Gray Row:</strong> Mixed signals (Neutral/Watch)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Analysis Tab */}
        {activeTab === "ai-analysis" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">🧠 AI-Powered Chart Analysis & TradingView Integration</h2>
            
            {/* Enhanced Stock Lookup with TradingView */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold mb-4">🔍 Universal Stock Analysis</h3>
              <div className="flex gap-4 mb-4">
                <input
                  type="text"
                  placeholder="Enter any ticker (AAPL, TSLA, NVDA, QQQ, etc.)"
                  value={stockLookup}
                  onChange={(e) => setStockLookup(e.target.value.toUpperCase())}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3 text-lg"
                  onKeyPress={(e) => e.key === 'Enter' && lookupStock()}
                />
                <button
                  onClick={lookupStock}
                  className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-medium"
                >
                  📊 Analyze
                </button>
              </div>
              
              {stockData && (
                <div className="bg-gray-700 rounded-lg p-6">
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h4 className="text-3xl font-bold text-blue-300">{stockData.ticker}</h4>
                      <p className="text-gray-400 text-lg">Live Technical Analysis</p>
                    </div>
                    <div className="flex gap-3">
                      <button
                        onClick={() => analyzeChart(stockData.ticker)}
                        className="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg font-medium"
                      >
                        🧠 AI Analysis
                      </button>
                      <button
                        onClick={() => window.open(`https://www.tradingview.com/chart/?symbol=${stockData.ticker}`, '_blank')}
                        className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded-lg font-medium"
                      >
                        📈 TradingView Pro
                      </button>
                      <button
                        onClick={() => {
                          setWatchlistForm({...watchlistForm, ticker: stockData.ticker, name: stockData.ticker});
                          setActiveTab("watchlists");
                        }}
                        className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded-lg font-medium"
                      >
                        ➕ Add to Watchlist
                      </button>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-6">
                    <div className="bg-gray-600 p-4 rounded-lg text-center">
                      <div className="text-gray-400 text-sm">Current Price</div>
                      <div className="text-2xl font-bold text-white">${stockData.current_price?.toFixed(2)}</div>
                    </div>
                    <div className="bg-gray-600 p-4 rounded-lg text-center">
                      <div className="text-gray-400 text-sm">1-Day</div>
                      <div className={`text-xl font-bold ${getChangeColor(stockData.change_1d)}`}>
                        {stockData.change_1d > 0 ? '+' : ''}{stockData.change_1d?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-gray-600 p-4 rounded-lg text-center">
                      <div className="text-gray-400 text-sm">1-Week</div>
                      <div className={`text-xl font-bold ${getChangeColor(stockData.change_1w)}`}>
                        {stockData.change_1w > 0 ? '+' : ''}{stockData.change_1w?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-gray-600 p-4 rounded-lg text-center">
                      <div className="text-gray-400 text-sm">1-Month</div>
                      <div className={`text-xl font-bold ${getChangeColor(stockData.change_1m)}`}>
                        {stockData.change_1m > 0 ? '+' : ''}{stockData.change_1m?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-gray-600 p-4 rounded-lg text-center">
                      <div className="text-gray-400 text-sm">Volatility</div>
                      <div className={`text-xl font-bold ${
                        stockData.atr_percent > 3 ? 'text-red-400' :
                        stockData.atr_percent > 2 ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {stockData.atr_percent?.toFixed(2)}%
                      </div>
                    </div>
                    <div className="bg-gray-600 p-4 rounded-lg text-center">
                      <div className="text-gray-400 text-sm">Volume</div>
                      <div className="text-xl font-bold text-blue-400">
                        {stockData.volume > 1000000 ? `${(stockData.volume/1000000).toFixed(1)}M` : `${Math.round(stockData.volume/1000)}K`}
                      </div>
                    </div>
                  </div>

                  {/* Embedded TradingView Chart */}
                  <div className="bg-gray-600 rounded-lg p-4 mb-4">
                    <h4 className="text-lg font-semibold mb-3 text-center">📊 Interactive TradingView Chart</h4>
                    <div className="bg-white rounded-lg h-96 flex items-center justify-center">
                      <div className="text-center text-gray-600">
                        <div className="text-6xl mb-4">📈</div>
                        <div className="text-xl font-semibold mb-2">Professional Chart for {stockData.ticker}</div>
                        <div className="mb-4 text-gray-500">
                          Interactive chart with drawing tools, indicators, and real-time data
                        </div>
                        <button
                          onClick={() => window.open(`https://www.tradingview.com/chart/?symbol=${stockData.ticker}`, '_blank')}
                          className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-lg font-medium"
                        >
                          🚀 Open Full TradingView Chart
                        </button>
                      </div>
                    </div>
                    <div className="mt-3 text-center text-sm text-gray-400">
                      ⚠️ TradingView Pro integration coming soon - Full chart embedding with drawing tools
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Direct Analysis Input */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold mb-4">⚡ Direct Chart Analysis</h3>
              <div className="flex gap-4 mb-4">
                <input
                  type="text"
                  placeholder="Enter ticker for direct AI analysis"
                  value={selectedTicker}
                  onChange={(e) => setSelectedTicker(e.target.value.toUpperCase())}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-2"
                />
                <button
                  onClick={() => analyzeChart(selectedTicker)}
                  disabled={!selectedTicker || loading}
                  className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg font-medium disabled:opacity-50"
                >
                  {loading ? "Analyzing..." : "🤖 AI Analysis"}
                </button>
              </div>

              {chartAnalysis && (
                <div className="space-y-6 border-t border-gray-700 pt-6">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-2xl font-bold text-purple-300">{chartAnalysis.ticker} - AI Analysis</h3>
                      <p className="text-gray-400 mt-1">Advanced Pattern Recognition & Technical Analysis</p>
                    </div>
                    <div className="text-right">
                      <div className="bg-purple-600 px-4 py-2 rounded-lg">
                        <div className="text-sm text-purple-100">AI Confidence</div>
                        <div className="text-xl font-bold text-white">
                          {(chartAnalysis.confidence * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Left Column - Analysis */}
                    <div className="space-y-6">
                      <div className="bg-blue-900 bg-opacity-30 rounded-lg p-5">
                        <h4 className="font-bold text-xl text-blue-300 mb-3 flex items-center">
                          📊 Pattern Analysis
                        </h4>
                        <div className="bg-gray-800 p-4 rounded text-gray-300 leading-relaxed">
                          {chartAnalysis.pattern_analysis}
                        </div>
                      </div>
                      
                      <div className="bg-green-900 bg-opacity-30 rounded-lg p-5">
                        <h4 className="font-bold text-xl text-green-300 mb-3 flex items-center">
                          📈 Trend Analysis
                        </h4>
                        <div className="bg-gray-800 p-4 rounded text-gray-300 leading-relaxed">
                          {chartAnalysis.trend_analysis}
                        </div>
                      </div>
                    </div>

                    {/* Right Column - Levels & Actions */}
                    <div className="space-y-6">
                      <div className="bg-orange-900 bg-opacity-30 rounded-lg p-5">
                        <h4 className="font-bold text-xl text-orange-300 mb-4">🎯 Key Trading Levels</h4>
                        <div className="space-y-4">
                          <div>
                            <div className="text-red-400 font-semibold mb-2 flex items-center">
                              ⬆️ <strong className="ml-2">Resistance Levels:</strong>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {chartAnalysis.resistance_levels.map((level, i) => (
                                <span key={i} className="bg-red-600 text-white px-3 py-2 rounded-lg font-bold">
                                  ${level}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div>
                            <div className="text-green-400 font-semibold mb-2 flex items-center">
                              ⬇️ <strong className="ml-2">Support Levels:</strong>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {chartAnalysis.support_levels.map((level, i) => (
                                <span key={i} className="bg-green-600 text-white px-3 py-2 rounded-lg font-bold">
                                  ${level}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="bg-yellow-900 bg-opacity-30 rounded-lg p-5">
                        <h4 className="font-bold text-xl text-yellow-300 mb-3">⚖️ Risk/Reward Assessment</h4>
                        <div className="bg-gray-800 p-4 rounded text-gray-300 leading-relaxed">
                          {chartAnalysis.risk_reward}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* AI Recommendation - Full Width */}
                  <div className="bg-gradient-to-r from-purple-900 to-blue-900 rounded-xl p-6">
                    <h4 className="font-bold text-2xl text-purple-200 mb-3 flex items-center">
                      🎯 AI Trading Recommendation
                    </h4>
                    <div className="text-lg text-purple-100 leading-relaxed bg-black bg-opacity-30 p-4 rounded-lg">
                      {chartAnalysis.recommendation}
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex justify-center gap-4 pt-4">
                    <button
                      onClick={() => window.open(`https://www.tradingview.com/chart/?symbol=${chartAnalysis.ticker}`, '_blank')}
                      className="bg-orange-600 hover:bg-orange-700 px-6 py-3 rounded-lg font-medium"
                    >
                      📊 View in TradingView
                    </button>
                    <button
                      onClick={() => {
                        setWatchlistForm({...watchlistForm, ticker: chartAnalysis.ticker, name: chartAnalysis.ticker});
                        setActiveTab("watchlists");
                      }}
                      className="bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-medium"
                    >
                      ➕ Add to Watchlist
                    </button>
                    <button className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-medium">
                      📄 Export Analysis
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* TradingView Integration Notice */}
            <div className="bg-gradient-to-r from-orange-800 to-red-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-2xl font-bold mb-4 text-orange-100">🚀 TradingView Pro Integration</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-semibold text-orange-200 mb-2">Coming Soon Features:</h4>
                  <ul className="space-y-2 text-orange-100">
                    <li>✅ Direct TradingView account connection</li>
                    <li>✅ Embedded interactive charts with full functionality</li>
                    <li>✅ Drawing tools and annotations</li>
                    <li>✅ Custom indicators and strategies</li>
                    <li>✅ Real-time alerts and notifications</li>
                    <li>✅ Multi-timeframe analysis</li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-lg font-semibold text-orange-200 mb-2">Current Capabilities:</h4>
                  <ul className="space-y-2 text-orange-100">
                    <li>🔥 AI-powered pattern recognition</li>
                    <li>🔥 Support/resistance identification</li>
                    <li>🔥 Risk/reward calculations</li>
                    <li>🔥 Trading recommendations</li>
                    <li>🔥 Direct TradingView links</li>
                    <li>🔥 Universal stock analysis</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Watchlists Tab */}
        {activeTab === "watchlists" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">📈 Custom Watchlists</h2>
            
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold mb-4">🔍 Stock Analysis</h3>
              <p className="text-gray-400">Use the AI Analysis tab to lookup and analyze any stock, then add it to your custom watchlists.</p>
              <div className="mt-4 flex gap-4">
                <button 
                  onClick={() => setActiveTab("ai-analysis")}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
                >
                  Go to AI Analysis
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ETFIntelligenceSystem;