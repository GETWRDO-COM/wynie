import React, { useState, useEffect, useCallback } from 'react';
import { FaRobot, FaSearch, FaPlus, FaTrash, FaChartLine, FaTrademark, FaSpinner, FaEye } from 'react-icons/fa';

const AIAnalysisTab = ({ api, addToWatchlist }) => {
  const [selectedStock, setSelectedStock] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [watchlists, setWatchlists] = useState([]);
  const [tradingViewAccount, setTradingViewAccount] = useState({ connected: false });
  const [tvUsername, setTvUsername] = useState('');
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    fetchWatchlists();
    checkTradingViewAccount();
  }, []);

  const fetchWatchlists = async () => {
    try {
      const response = await api.get('/api/watchlists/custom');
      setWatchlists(response.data);
    } catch (err) {
      console.error('Failed to fetch watchlists:', err);
    }
  };

  const checkTradingViewAccount = async () => {
    try {
      const response = await api.get('/api/tradingview/account');
      setTradingViewAccount(response.data);
      if (response.data.connected) {
        setTvUsername(response.data.account?.username || '');
      }
    } catch (err) {
      console.error('Failed to check TradingView account:', err);
    }
  };

  const connectTradingView = async () => {
    if (!tvUsername.trim()) {
      alert('Please enter your TradingView username.');
      return;
    }

    setConnecting(true);
    try {
      await api.post('/api/tradingview/connect', {
        username: tvUsername,
        access_token: null
      });
      
      setTradingViewAccount({ connected: true });
      alert('TradingView account connected successfully!');
    } catch (err) {
      alert('Failed to connect TradingView account. Please try again.');
    } finally {
      setConnecting(false);
    }
  };

  const searchStocks = useCallback(async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await api.get(`/api/companies/search?query=${encodeURIComponent(query)}&limit=20`);
      setSearchResults(response.data.companies);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, [api]);

  const analyzeStock = async (ticker) => {
    setAnalyzing(true);
    try {
      // Get company details
      const companyResponse = await api.get(`/api/companies/${ticker}`);
      const companyData = companyResponse.data;

      // Get AI chart analysis
      const analysisResponse = await api.get(`/api/charts/${ticker}/analysis`);
      const chartAnalysis = analysisResponse.data;

      setSelectedStock(companyData.company);
      setAnalysis(chartAnalysis);
    } catch (err) {
      alert('Failed to analyze stock. Please try again.');
      console.error('Analysis error:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const openTradingViewChart = (ticker) => {
    const url = `https://www.tradingview.com/chart/?symbol=${ticker}`;
    window.open(url, '_blank', 'width=1200,height=800');
  };

  const addStockToWatchlist = async (ticker, name, listName) => {
    try {
      // Create watchlist if it doesn't exist
      const existingList = watchlists.find(wl => wl.name === listName);
      if (!existingList) {
        await api.post('/api/watchlists/lists', {
          name: listName,
          description: `Custom watchlist: ${listName}`,
          color: '#3B82F6'
        });
      }

      await api.post(`/api/watchlists/custom/${listName}/add-stock`, {
        ticker: ticker,
        name: name,
        notes: 'Added via AI Analysis',
        priority: 2
      });

      await fetchWatchlists();
      alert(`Added ${ticker} to ${listName} watchlist!`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add to watchlist');
    }
  };

  const removeFromWatchlist = async (ticker, listName) => {
    try {
      await api.delete(`/api/watchlists/custom/${listName}/remove-stock/${ticker}`);
      await fetchWatchlists();
      alert(`Removed ${ticker} from ${listName} watchlist!`);
    } catch (err) {
      alert('Failed to remove from watchlist');
    }
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => searchStocks(searchQuery), 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery, searchStocks]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
        <h2 className="text-3xl font-bold text-white flex items-center mb-4">
          <FaRobot className="mr-3 text-blue-400" />
          AI Analysis & Dynamic Watchlists
        </h2>
        
        {/* Universal Stock Search */}
        <div className="relative mb-6">
          <div className="flex items-center">
            <FaSearch className="absolute left-4 text-gray-400 z-10" />
            <input
              type="text"
              placeholder="🔍 Search any stock or ETF (AAPL, Apple, Tesla, Microsoft, etc.)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {searching && (
              <FaSpinner className="absolute right-4 animate-spin text-blue-400" />
            )}
          </div>
          
          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="absolute top-full left-0 right-0 bg-gray-800 border border-gray-600 rounded-lg mt-1 max-h-64 overflow-y-auto z-20 shadow-xl">
              {searchResults.map((company) => (
                <div
                  key={company.ticker}
                  className="p-4 hover:bg-gray-700 cursor-pointer border-b border-gray-700 last:border-0"
                  onClick={() => {
                    analyzeStock(company.ticker);
                    setSearchQuery('');
                    setSearchResults([]);
                  }}
                >
                  <div className="flex items-center gap-3">
                    <img
                      src={company.logo_url}
                      alt={`${company.company_name} logo`}
                      className="w-10 h-10 rounded-full bg-gray-600"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <span className="font-bold text-blue-300 text-xl">{company.ticker}</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          company.rotation_status === 'Rotating In' ? 'bg-green-900 text-green-300' :
                          company.rotation_status === 'Rotating Out' ? 'bg-red-900 text-red-300' :
                          'bg-gray-600 text-gray-300'
                        }`}>
                          {company.rotation_status}
                        </span>
                      </div>
                      <div className="text-gray-300 font-medium text-lg">{company.company_name}</div>
                      <div className="text-gray-400 text-sm">{company.sector} • {company.industry}</div>
                      {company.market_cap > 0 && (
                        <div className="text-gray-400 text-xs">
                          Market Cap: ${(company.market_cap / 1e9).toFixed(1)}B
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* TradingView Integration */}
        <div className="bg-gray-700 rounded-lg p-4 mb-4">
          <h4 className="font-semibold text-white mb-3 flex items-center">
            <FaTrademark className="mr-2 text-orange-500" />
            TradingView Advanced Charts & Drawing Tools
          </h4>
          
          {!tradingViewAccount.connected ? (
            <div className="space-y-3">
              <p className="text-gray-300 text-sm">Connect your TradingView account for advanced charting:</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="TradingView Username"
                  value={tvUsername}
                  onChange={(e) => setTvUsername(e.target.value)}
                  className="flex-1 px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white"
                />
                <button
                  onClick={connectTradingView}
                  disabled={connecting}
                  className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 px-6 py-2 rounded text-white font-medium"
                >
                  {connecting ? 'Connecting...' : 'Connect'}
                </button>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-300">
                <div>✅ Professional chart drawing tools</div>
                <div>✅ Advanced technical indicators</div>
                <div>✅ Save custom chart layouts</div>
                <div>✅ Multiple timeframes & studies</div>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="text-green-400 font-semibold">✅ Connected: {tvUsername}</div>
              <div className="flex gap-2">
                <button
                  onClick={() => selectedStock && openTradingViewChart(selectedStock.ticker)}
                  disabled={!selectedStock}
                  className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 px-4 py-2 rounded text-white font-medium"
                >
                  📊 Open {selectedStock?.ticker || 'Stock'} Chart
                </button>
                <button
                  onClick={() => openTradingViewChart('SPY')}
                  className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded text-white"
                >
                  📈 Market Overview
                </button>
              </div>
              <p className="text-gray-400 text-sm">
                Charts open in new window with full drawing capabilities, indicators, and saving features.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Analysis Results */}
      {analyzing && (
        <div className="bg-gray-800 rounded-xl p-8 shadow-lg text-center">
          <FaSpinner className="animate-spin text-4xl text-blue-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Analyzing Chart...</h3>
          <p className="text-gray-400">AI is processing technical indicators, patterns, and market data...</p>
        </div>
      )}

      {selectedStock && analysis && !analyzing && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Company Information */}
          <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
            <div className="flex items-center gap-4 mb-4">
              <img
                src={selectedStock.logo_url}
                alt={`${selectedStock.company_name} logo`}
                className="w-16 h-16 rounded-full bg-gray-600"
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
              <div>
                <h3 className="text-2xl font-bold text-white">{selectedStock.ticker}</h3>
                <p className="text-gray-300 text-lg">{selectedStock.company_name}</p>
                <p className="text-gray-400">{selectedStock.sector} • {selectedStock.industry}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-gray-400 text-sm">Market Cap</div>
                <div className="text-white font-semibold">
                  ${selectedStock.market_cap > 0 ? (selectedStock.market_cap / 1e9).toFixed(1) + 'B' : 'N/A'}
                </div>
              </div>
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="text-gray-400 text-sm">Sector Rotation</div>
                <div className={`font-semibold ${
                  selectedStock.rotation_status === 'Rotating In' ? 'text-green-400' :
                  selectedStock.rotation_status === 'Rotating Out' ? 'text-red-400' :
                  'text-gray-400'
                }`}>
                  {selectedStock.rotation_status}
                </div>
              </div>
            </div>

            <div className="mb-4">
              <h4 className="text-lg font-semibold text-white mb-2">Company Description</h4>
              <p className="text-gray-300 text-sm">{selectedStock.description || 'No description available.'}</p>
              {selectedStock.website && (
                <a 
                  href={selectedStock.website} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 text-sm mt-2 inline-block"
                >
                  🌐 Visit Website
                </a>
              )}
            </div>

            {/* Add to Watchlist Actions */}
            <div className="space-y-3">
              <h4 className="text-lg font-semibold text-white">Add to Watchlist</h4>
              <div className="grid grid-cols-2 gap-2">
                {['Growth', 'Swing', 'Income', 'Research'].map((listName) => (
                  <button
                    key={listName}
                    onClick={() => addStockToWatchlist(selectedStock.ticker, selectedStock.company_name, listName)}
                    className="bg-green-600 hover:bg-green-700 px-3 py-2 rounded text-sm font-medium flex items-center justify-center gap-1"
                  >
                    <FaPlus />
                    {listName}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* AI Analysis Results */}
          <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
            <h3 className="text-2xl font-bold text-white mb-4 flex items-center">
              <FaRobot className="mr-2 text-blue-400" />
              AI Technical Analysis
            </h3>

            <div className="space-y-4">
              {/* Confidence Score */}
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-gray-300">Analysis Confidence</span>
                  <span className="text-blue-400 font-bold">{(analysis.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{ width: `${analysis.confidence * 100}%` }}
                  />
                </div>
              </div>

              {/* Pattern Analysis */}
              <div className="bg-gray-700 rounded-lg p-4">
                <h4 className="text-white font-semibold mb-2">📊 Pattern Analysis</h4>
                <p className="text-gray-300 text-sm whitespace-pre-wrap">{analysis.pattern_analysis}</p>
              </div>

              {/* Support & Resistance */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="text-green-400 font-semibold mb-2">📈 Support Levels</h4>
                  {analysis.support_levels.map((level, index) => (
                    <div key={index} className="text-green-300 font-mono">
                      ${level}
                    </div>
                  ))}
                </div>
                <div className="bg-gray-700 rounded-lg p-4">
                  <h4 className="text-red-400 font-semibold mb-2">📉 Resistance Levels</h4>
                  {analysis.resistance_levels.map((level, index) => (
                    <div key={index} className="text-red-300 font-mono">
                      ${level}
                    </div>
                  ))}
                </div>
              </div>

              {/* Trend Analysis */}
              <div className="bg-gray-700 rounded-lg p-4">
                <h4 className="text-white font-semibold mb-2">📈 Trend Analysis</h4>
                <p className="text-gray-300 text-sm">{analysis.trend_analysis}</p>
              </div>

              {/* Risk/Reward */}
              <div className="bg-gray-700 rounded-lg p-4">
                <h4 className="text-yellow-400 font-semibold mb-2">⚖️ Risk/Reward</h4>
                <p className="text-gray-300 text-sm">{analysis.risk_reward}</p>
              </div>

              {/* Trading Recommendation */}
              <div className="bg-gray-700 rounded-lg p-4">
                <h4 className="text-blue-400 font-semibold mb-2">🎯 Trading Recommendation</h4>
                <p className="text-white font-medium">{analysis.recommendation}</p>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => analyzeStock(selectedStock.ticker)}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded font-medium flex items-center gap-2"
                >
                  <FaRobot />
                  Re-analyze
                </button>
                {tradingViewAccount.connected && (
                  <button
                    onClick={() => openTradingViewChart(selectedStock.ticker)}
                    className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded font-medium flex items-center gap-2"
                  >
                    <FaChartLine />
                    Open Chart
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Dynamic Watchlists */}
      <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
        <h3 className="text-2xl font-bold text-white mb-4">📋 Dynamic Watchlists</h3>
        
        {watchlists.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <p>No watchlists yet. Add stocks using the search above!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {watchlists.map((watchlist) => (
              <div key={watchlist.id} className="bg-gray-700 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <h4 className="font-semibold text-white">{watchlist.name}</h4>
                  <div className="text-sm text-gray-400">
                    {watchlist.stocks?.length || 0} stocks
                  </div>
                </div>
                
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {watchlist.stocks?.map((stock) => (
                    <div key={stock.id} className="flex justify-between items-center bg-gray-600 rounded p-2">
                      <div>
                        <div className="font-semibold text-blue-300">{stock.ticker}</div>
                        <div className="text-xs text-gray-400">{stock.name?.length > 20 ? stock.name.substring(0, 20) + '...' : stock.name}</div>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => analyzeStock(stock.ticker)}
                          className="bg-blue-600 hover:bg-blue-700 p-1 rounded text-xs"
                          title="Analyze"
                        >
                          <FaEye />
                        </button>
                        <button
                          onClick={() => removeFromWatchlist(stock.ticker, watchlist.name)}
                          className="bg-red-600 hover:bg-red-700 p-1 rounded text-xs"
                          title="Remove"
                        >
                          <FaTrash />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {(!watchlist.stocks || watchlist.stocks.length === 0) && (
                  <div className="text-center text-gray-400 text-sm py-4">
                    Empty watchlist
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {!selectedStock && !analyzing && (
        <div className="bg-gray-800 rounded-xl p-8 text-center shadow-lg">
          <FaSearch className="text-6xl text-gray-600 mx-auto mb-4" />
          <h3 className="text-2xl font-bold text-white mb-2">Search for Any Stock or ETF</h3>
          <p className="text-gray-400 text-lg mb-4">
            Use the search box above to find stocks by ticker symbol or company name
          </p>
          <p className="text-gray-500 text-sm">
            Examples: AAPL, Apple, Tesla, Microsoft, Amazon, Google, etc.
          </p>
        </div>
      )}
    </div>
  );
};

export default AIAnalysisTab;