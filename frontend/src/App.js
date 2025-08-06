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
    const interval = setInterval(fetchDashboardData, 30000); // Update every 30 seconds
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
              <h1 className="text-3xl font-bold text-white">📊 ETF Intelligence System</h1>
              <p className="text-gray-300 mt-1">Real-time market intelligence for swing traders</p>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={updateETFs}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg font-medium disabled:opacity-50"
              >
                {loading ? "Updating..." : "🔄 Update Data"}
              </button>
              <div className="text-sm text-gray-300">
                Last updated: {new Date().toLocaleTimeString()}
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
              { id: "dashboard", label: "📈 Dashboard" },
              { id: "etfs", label: "📊 ETF Tracker" },
              { id: "watchlists", label: "📋 Watchlists" },
              { id: "analysis", label: "🧠 AI Analysis" }
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
            {/* Market Score Card */}
            {marketScore && (
              <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
                <h2 className="text-2xl font-bold mb-4">🎯 Market Situational Awareness</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className={`text-4xl font-bold p-4 rounded-lg ${getScoreColor(marketScore.total_score)}`}>
                      {marketScore.total_score}/40
                    </div>
                    <p className="text-lg font-semibold mt-2">{marketScore.classification}</p>
                  </div>
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-semibold mb-2">Current Recommendation:</h3>
                    <p className="text-gray-300 mb-4">{marketScore.recommendation}</p>
                    <div className="grid grid-cols-4 gap-2 text-sm">
                      <div>SATA: {marketScore.sata_score}/4</div>
                      <div>ADX: {marketScore.adx_score}/4</div>
                      <div>VIX: {marketScore.vix_score}/4</div>
                      <div>ATR: {marketScore.atr_score}/4</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Market Leaders */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h2 className="text-2xl font-bold mb-4">🚀 Current Market Leaders</h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-2">Ticker</th>
                      <th className="text-left py-2">Sector</th>
                      <th className="text-left py-2">1M Change</th>
                      <th className="text-left py-2">Relative Strength</th>
                      <th className="text-left py-2">SATA</th>
                      <th className="text-left py-2">Pattern</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaders.slice(0, 10).map((etf) => (
                      <tr key={etf.ticker} className="border-b border-gray-700 hover:bg-gray-700">
                        <td className="py-2 font-semibold">{etf.ticker}</td>
                        <td className="py-2 text-gray-300">{etf.sector}</td>
                        <td className={`py-2 font-semibold ${getChangeColor(etf.change_1m)}`}>
                          {etf.change_1m > 0 ? '+' : ''}{etf.change_1m.toFixed(2)}%
                        </td>
                        <td className="py-2">{getRSBadge(etf.relative_strength_1m)}</td>
                        <td className="py-2">{etf.sata_score}/10</td>
                        <td className="py-2">
                          <span className={`px-2 py-1 text-xs rounded ${
                            etf.gmma_pattern === 'RWB' ? 'bg-green-100 text-green-800' :
                            etf.gmma_pattern === 'BWR' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {etf.gmma_pattern}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ETF Tracker Tab */}
        {activeTab === "etfs" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">ETF Universe Tracker</h2>
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
            </div>

            <div className="bg-gray-800 rounded-xl p-6 shadow-lg overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3">Ticker</th>
                    <th className="text-left py-3">Name</th>
                    <th className="text-left py-3">Price</th>
                    <th className="text-left py-3">1D</th>
                    <th className="text-left py-3">1W</th>
                    <th className="text-left py-3">1M</th>
                    <th className="text-left py-3">RS 1M</th>
                    <th className="text-left py-3">ATR%</th>
                    <th className="text-left py-3">SATA</th>
                    <th className="text-left py-3">Trend</th>
                    <th className="text-left py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEtfs.map((etf) => (
                    <tr key={etf.ticker} className="border-b border-gray-700 hover:bg-gray-700">
                      <td className="py-3 font-semibold">{etf.ticker}</td>
                      <td className="py-3 text-gray-300 max-w-xs truncate">{etf.name}</td>
                      <td className="py-3">${etf.current_price.toFixed(2)}</td>
                      <td className={`py-3 font-semibold ${getChangeColor(etf.change_1d)}`}>
                        {etf.change_1d > 0 ? '+' : ''}{etf.change_1d.toFixed(2)}%
                      </td>
                      <td className={`py-3 font-semibold ${getChangeColor(etf.change_1w)}`}>
                        {etf.change_1w > 0 ? '+' : ''}{etf.change_1w.toFixed(2)}%
                      </td>
                      <td className={`py-3 font-semibold ${getChangeColor(etf.change_1m)}`}>
                        {etf.change_1m > 0 ? '+' : ''}{etf.change_1m.toFixed(2)}%
                      </td>
                      <td className="py-3">{getRSBadge(etf.relative_strength_1m)}</td>
                      <td className="py-3">{etf.atr_percent.toFixed(2)}%</td>
                      <td className="py-3">{etf.sata_score}/10</td>
                      <td className="py-3">
                        <div className="flex space-x-1">
                          <span className={`w-6 h-6 rounded text-xs flex items-center justify-center ${
                            etf.sma20_trend === 'U' ? 'bg-green-500' : 
                            etf.sma20_trend === 'D' ? 'bg-red-500' : 'bg-gray-500'
                          }`}>
                            {etf.sma20_trend}
                          </span>
                        </div>
                      </td>
                      <td className="py-3">
                        <button
                          onClick={() => analyzeChart(etf.ticker)}
                          className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
                        >
                          📈 Analyze
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Watchlists Tab */}
        {activeTab === "watchlists" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">Stock Watchlists</h2>
            
            {/* Add to Watchlist Form */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold mb-4">Add New Stock</h3>
              <form onSubmit={addToWatchlist} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                  type="text"
                  placeholder="Ticker (e.g., AAPL)"
                  value={watchlistForm.ticker}
                  onChange={(e) => setWatchlistForm({...watchlistForm, ticker: e.target.value.toUpperCase()})}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2"
                  required
                />
                <input
                  type="text"
                  placeholder="Company Name"
                  value={watchlistForm.name}
                  onChange={(e) => setWatchlistForm({...watchlistForm, name: e.target.value})}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2"
                  required
                />
                <select
                  value={watchlistForm.list_name}
                  onChange={(e) => setWatchlistForm({...watchlistForm, list_name: e.target.value})}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2"
                >
                  <option>Growth Watchlist</option>
                  <option>Swing Portfolio</option>
                  <option>Income ETFs</option>
                  <option>Breakout Candidates</option>
                  <option>High Momentum</option>
                </select>
                <input
                  type="text"
                  placeholder="Tags (comma separated)"
                  value={watchlistForm.tags}
                  onChange={(e) => setWatchlistForm({...watchlistForm, tags: e.target.value})}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2"
                />
                <input
                  type="text"
                  placeholder="Notes"
                  value={watchlistForm.notes}
                  onChange={(e) => setWatchlistForm({...watchlistForm, notes: e.target.value})}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2"
                />
                <button
                  type="submit"
                  className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded font-medium"
                >
                  Add to Watchlist
                </button>
              </form>
            </div>

            {/* Watchlist Display */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Your Watchlists</h3>
                <button
                  onClick={fetchWatchlists}
                  className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm"
                >
                  Refresh
                </button>
              </div>
              {watchlists.length === 0 ? (
                <p className="text-gray-400">No stocks in watchlists yet. Add some above!</p>
              ) : (
                <div className="space-y-4">
                  {/* Group by list_name */}
                  {Object.entries(
                    watchlists.reduce((acc, item) => {
                      if (!acc[item.list_name]) acc[item.list_name] = [];
                      acc[item.list_name].push(item);
                      return acc;
                    }, {})
                  ).map(([listName, items]) => (
                    <div key={listName} className="border border-gray-700 rounded-lg p-4">
                      <h4 className="font-semibold text-lg mb-3">{listName}</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {items.map((item) => (
                          <div key={item.id} className="bg-gray-700 rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h5 className="font-semibold">{item.ticker}</h5>
                              <button
                                onClick={() => analyzeChart(item.ticker)}
                                className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs"
                              >
                                📈
                              </button>
                            </div>
                            <p className="text-sm text-gray-300 mb-2">{item.name}</p>
                            {item.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mb-2">
                                {item.tags.map((tag, index) => (
                                  <span key={index} className="bg-blue-600 text-xs px-2 py-1 rounded">
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                            {item.notes && <p className="text-xs text-gray-400">{item.notes}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* AI Analysis Tab */}
        {activeTab === "analysis" && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold">🧠 AI Chart Analysis</h2>
            
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="mb-4">
                <input
                  type="text"
                  placeholder="Enter ticker symbol (e.g., TQQQ, AAPL)"
                  value={selectedTicker}
                  onChange={(e) => setSelectedTicker(e.target.value.toUpperCase())}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2 mr-4"
                />
                <button
                  onClick={() => analyzeChart(selectedTicker)}
                  disabled={!selectedTicker}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-medium disabled:opacity-50"
                >
                  🔍 Analyze Chart
                </button>
              </div>

              {chartAnalysis && (
                <div className="space-y-4 border-t border-gray-700 pt-4">
                  <div className="flex justify-between items-start">
                    <h3 className="text-xl font-semibold">{chartAnalysis.ticker} Analysis</h3>
                    <span className="bg-blue-600 px-3 py-1 rounded text-sm">
                      Confidence: {(chartAnalysis.confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold mb-2">📊 Pattern Analysis</h4>
                      <p className="text-gray-300 mb-4">{chartAnalysis.pattern_analysis}</p>
                      
                      <h4 className="font-semibold mb-2">📈 Trend Analysis</h4>
                      <p className="text-gray-300 mb-4">{chartAnalysis.trend_analysis}</p>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-2">🎯 Key Levels</h4>
                      <div className="space-y-2 mb-4">
                        <div>
                          <strong className="text-red-400">Resistance:</strong> 
                          {chartAnalysis.resistance_levels.map((level, i) => (
                            <span key={i} className="ml-2 bg-red-100 text-red-800 px-2 py-1 rounded text-sm">
                              ${level}
                            </span>
                          ))}
                        </div>
                        <div>
                          <strong className="text-green-400">Support:</strong>
                          {chartAnalysis.support_levels.map((level, i) => (
                            <span key={i} className="ml-2 bg-green-100 text-green-800 px-2 py-1 rounded text-sm">
                              ${level}
                            </span>
                          ))}
                        </div>
                      </div>

                      <h4 className="font-semibold mb-2">⚖️ Risk/Reward</h4>
                      <p className="text-gray-300 mb-4">{chartAnalysis.risk_reward}</p>
                    </div>
                  </div>

                  <div className="bg-blue-900 bg-opacity-50 rounded-lg p-4">
                    <h4 className="font-semibold mb-2 text-blue-300">🎯 AI Recommendation</h4>
                    <p className="text-blue-100">{chartAnalysis.recommendation}</p>
                  </div>
                </div>
              )}
            </div>

            {/* TradingView Widget Placeholder */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-semibold mb-4">📈 Interactive Chart</h3>
              <div className="bg-gray-700 rounded-lg h-96 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-gray-400 mb-2">TradingView Chart Widget</p>
                  <p className="text-gray-500 text-sm">
                    {selectedTicker ? `Showing chart for ${selectedTicker}` : "Select a ticker to view chart"}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ETFIntelligenceSystem;