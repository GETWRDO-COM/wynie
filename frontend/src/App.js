import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { FaEye, FaEyeSlash, FaCog, FaSignOutAlt, FaLock, FaUser, FaRobot, FaChartLine, FaTable, FaTrademark, FaSpinner } from 'react-icons/fa';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Import the new components
import SwingAnalysisGrid from './components/SwingAnalysisGrid';
import AIAnalysisTab from './components/AIAnalysisTab';
import SpreadsheetTab from './components/SpreadsheetTab';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Get backend URL from environment variable
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: BACKEND_URL,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

// Authentication Component
const LoginForm = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ email: 'beetge@mwebbiz.co.za', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/auth/login', credentials);
      const { access_token, user } = response.data;
      
      localStorage.setItem('authToken', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      onLogin(user);
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!credentials.email) {
      setError('Please enter your email address first.');
      return;
    }

    try {
      const response = await api.post('/api/auth/forgot-password', { email: credentials.email });
      alert(response.data.message + '\n\n' + (response.data.temp_instructions || ''));
    } catch (err) {
      setError('Failed to send password reset instructions.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-800 flex items-center justify-center px-4">
      <div className="bg-gray-800 rounded-2xl shadow-2xl p-8 w-full max-w-md border border-gray-700">
        <div className="text-center mb-8">
          <div className="bg-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <FaLock className="text-2xl text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">ETF Intelligence</h1>
          <p className="text-gray-400">Secure Access Portal</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <FaUser className="inline mr-2" />
              Email Address
            </label>
            <input
              type="email"
              value={credentials.email}
              onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
              className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your email"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              <FaLock className="inline mr-2" />
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent pr-12"
                placeholder="Enter your password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white"
              >
                {showPassword ? <FaEyeSlash /> : <FaEye />}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-900 border border-red-700 rounded-lg p-3 text-red-300 text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition duration-200 flex items-center justify-center"
          >
            {loading ? (
              <>
                <FaSpinner className="animate-spin mr-2" />
                Signing In...
              </>
            ) : (
              'Sign In'
            )}
          </button>

          <div className="text-center">
            <button
              type="button"
              onClick={handleForgotPassword}
              className="text-blue-400 hover:text-blue-300 text-sm underline"
            >
              Forgot Password?
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Settings Modal Component
const SettingsModal = ({ isOpen, onClose, user }) => {
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      await api.post('/api/auth/settings', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password
      });
      
      setMessage('Password updated successfully!');
      setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update password.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-xl p-6 w-full max-w-md mx-4 border border-gray-700">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-white flex items-center">
            <FaCog className="mr-2" />
            Settings
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl"
          >
            ×
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-700 rounded-lg">
          <p className="text-gray-300 text-sm">Account: {user?.email}</p>
          <p className="text-gray-400 text-xs">Last Login: {user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}</p>
        </div>

        <form onSubmit={handleUpdatePassword} className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Change Password</h3>
          
          <input
            type="password"
            placeholder="Current Password"
            value={passwordData.current_password}
            onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400"
            required
          />
          
          <input
            type="password"
            placeholder="New Password"
            value={passwordData.new_password}
            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400"
            required
          />
          
          <input
            type="password"
            placeholder="Confirm New Password"
            value={passwordData.confirm_password}
            onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400"
            required
          />

          {error && <div className="text-red-400 text-sm">{error}</div>}
          {message && <div className="text-green-400 text-sm">{message}</div>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white py-2 rounded-lg"
          >
            {loading ? 'Updating...' : 'Update Password'}
          </button>
        </form>
      </div>
    </div>
  );
};

// AI Chat Component
const AIChat = ({ user }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState('latest');
  const [availableModels, setAvailableModels] = useState({});
  const [currentSession, setCurrentSession] = useState(null);
  const [ticker, setTicker] = useState('');
  const [includeChart, setIncludeChart] = useState(false);

  useEffect(() => {
    fetchAvailableModels();
    createNewSession();
  }, []);

  const fetchAvailableModels = async () => {
    try {
      const response = await api.get('/api/ai/models');
      setAvailableModels(response.data.models);
      setSelectedModel(response.data.recommended);
    } catch (err) {
      console.error('Failed to fetch AI models:', err);
    }
  };

  const createNewSession = async () => {
    try {
      const sessionData = {
        title: 'New Trading Chat',
        model: selectedModel
      };
      const response = await api.post('/api/ai/sessions', sessionData);
      setCurrentSession(response.data.id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create chat session:', err);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !currentSession) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await api.post('/api/ai/chat', {
        session_id: currentSession,
        message: inputMessage,
        model: selectedModel,
        ticker: includeChart ? ticker : null,
        include_chart_data: includeChart && ticker
      });

      const aiMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, aiMessage]);
      setInputMessage('');
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg h-[600px] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <FaRobot className="mr-2 text-blue-400" />
          AI Trading Assistant
        </h2>
        <div className="flex gap-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-1 text-white text-sm"
          >
            {Object.entries(availableModels).map(([key, model]) => (
              <option key={key} value={key}>
                {key === 'latest' ? `🚀 Latest (${model})` : `${key}`}
              </option>
            ))}
          </select>
          <button
            onClick={createNewSession}
            className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-lg text-white text-sm"
          >
            New Chat
          </button>
        </div>
      </div>

      {/* Chart Context Controls */}
      <div className="mb-4 p-3 bg-gray-700 rounded-lg">
        <div className="flex items-center gap-4">
          <label className="flex items-center text-sm text-gray-300">
            <input
              type="checkbox"
              checked={includeChart}
              onChange={(e) => setIncludeChart(e.target.checked)}
              className="mr-2"
            />
            Include Chart Analysis
          </label>
          {includeChart && (
            <input
              type="text"
              placeholder="Enter ticker (e.g., AAPL, SPY)"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="px-3 py-1 bg-gray-600 border border-gray-500 rounded text-white text-sm"
            />
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto mb-4 space-y-3">
        {messages.length === 0 && (
          <div className="text-gray-400 text-center py-8">
            <FaRobot className="text-4xl mx-auto mb-4 opacity-50" />
            <p>Welcome to your AI Trading Assistant!</p>
            <p className="text-sm mt-2">Ask me about market analysis, trading strategies, or specific stocks.</p>
          </div>
        )}
        {messages.map((message, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg ${
              message.role === 'user'
                ? 'bg-blue-600 ml-12 text-white'
                : 'bg-gray-700 mr-12 text-gray-100'
            }`}
          >
            <div className="text-sm opacity-75 mb-1">
              {message.role === 'user' ? 'You' : `AI (${selectedModel})`}
            </div>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        ))}
        {loading && (
          <div className="bg-gray-700 mr-12 p-3 rounded-lg">
            <div className="flex items-center text-gray-300">
              <FaSpinner className="animate-spin mr-2" />
              AI is thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={sendMessage} className="flex gap-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder={includeChart && ticker ? `Ask about ${ticker} chart...` : "Ask me about trading, markets, or analysis..."}
          className="flex-1 px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !inputMessage.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-4 py-2 rounded-lg text-white font-medium"
        >
          Send
        </button>
      </form>
    </div>
  );
};

// Enhanced Stock Search Component
const StockSearch = ({ onSelectStock }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchStocks = useCallback(async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await api.get(`/api/companies/search?query=${encodeURIComponent(searchQuery)}&limit=10`);
      setResults(response.data.companies);
    } catch (err) {
      console.error('Search failed:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => searchStocks(query), 300);
    return () => clearTimeout(timeoutId);
  }, [query, searchStocks]);

  return (
    <div className="relative">
      <input
        type="text"
        placeholder="Search stocks by name or ticker (AAPL, Apple, Tesla...)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      
      {loading && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <FaSpinner className="animate-spin text-blue-400" />
        </div>
      )}
      
      {results.length > 0 && (
        <div className="absolute top-full left-0 right-0 bg-gray-800 border border-gray-600 rounded-lg mt-1 max-h-64 overflow-y-auto z-10">
          {results.map((company) => (
            <div
              key={company.ticker}
              className="p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-700 last:border-0"
              onClick={() => {
                onSelectStock(company);
                setQuery('');
                setResults([]);
              }}
            >
              <div className="flex items-center gap-3">
                <img
                  src={company.logo_url}
                  alt={`${company.company_name} logo`}
                  className="w-8 h-8 rounded-full bg-gray-600"
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-blue-300 text-lg">{company.ticker}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      company.rotation_status === 'Rotating In' ? 'bg-green-900 text-green-300' :
                      company.rotation_status === 'Rotating Out' ? 'bg-red-900 text-red-300' :
                      'bg-gray-600 text-gray-300'
                    }`}>
                      {company.rotation_status}
                    </span>
                  </div>
                  <div className="text-gray-300 font-medium">{company.company_name}</div>
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
  );
};

// TradingView Integration Component
const TradingViewIntegration = ({ ticker }) => {
  const [account, setAccount] = useState({ connected: false });
  const [username, setUsername] = useState('');
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    checkTradingViewAccount();
  }, []);

  const checkTradingViewAccount = async () => {
    try {
      const response = await api.get('/api/tradingview/account');
      setAccount(response.data);
      if (response.data.connected) {
        setUsername(response.data.account?.username || '');
      }
    } catch (err) {
      console.error('Failed to check TradingView account:', err);
    }
  };

  const connectTradingViewAccount = async () => {
    if (!username.trim()) {
      alert('Please enter your TradingView username.');
      return;
    }

    setConnecting(true);
    try {
      await api.post('/api/tradingview/connect', {
        username: username,
        access_token: null // In production, you'd handle OAuth flow
      });
      
      setAccount({ connected: true });
      alert('TradingView account connected successfully! You can now use advanced chart features.');
    } catch (err) {
      alert('Failed to connect TradingView account. Please try again.');
    } finally {
      setConnecting(false);
    }
  };

  const openTradingViewChart = (symbol) => {
    const url = `https://www.tradingview.com/chart/?symbol=${symbol}`;
    window.open(url, '_blank', 'width=1200,height=800');
  };

  return (
    <div className="bg-gray-700 rounded-lg p-4">
      <h4 className="font-semibold text-white mb-3 flex items-center">
        <FaTrademark className="mr-2 text-orange-500" />
        TradingView Integration
      </h4>
      
      {!account.connected ? (
        <div className="space-y-3">
          <p className="text-gray-300 text-sm">Connect your TradingView account for advanced charting features:</p>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="TradingView Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white text-sm"
            />
            <button
              onClick={connectTradingViewAccount}
              disabled={connecting}
              className="bg-orange-600 hover:bg-orange-700 disabled:opacity-50 px-4 py-2 rounded text-white text-sm font-medium"
            >
              {connecting ? 'Connecting...' : 'Connect'}
            </button>
          </div>
          <p className="text-gray-400 text-xs">
            ✅ Chart drawing tools<br />
            ✅ Advanced indicators<br />
            ✅ Save custom layouts
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="text-green-400 text-sm">✅ Connected: {username}</div>
          <div className="flex gap-2">
            <button
              onClick={() => openTradingViewChart(ticker)}
              className="bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded text-white text-sm font-medium"
            >
              Open {ticker} Chart
            </button>
            <button
              onClick={() => openTradingViewChart('SPY')}
              className="bg-gray-600 hover:bg-gray-500 px-3 py-2 rounded text-white text-sm"
            >
              Market Overview
            </button>
          </div>
          <p className="text-gray-400 text-xs">
            Your charts will open in a new window with full drawing capabilities.
          </p>
        </div>
      )}
    </div>
  );
};

// Chart Component for Indices
const IndexChart = ({ data, title, timeframe }) => {
  const chartData = {
    labels: data?.dates || [],
    datasets: [
      {
        label: title,
        data: data?.prices || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
        display: false,
        grid: {
          color: 'rgba(75, 85, 99, 0.3)',
        },
      },
      y: {
        display: true,
        grid: {
          color: 'rgba(75, 85, 99, 0.3)',
        },
        ticks: {
          color: 'rgb(156, 163, 175)',
          font: {
            size: 10,
          },
        },
      },
    },
  };

  return (
    <div className="h-32">
      <Line data={chartData} options={options} />
    </div>
  );
};

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  
  // Dashboard data
  const [dashboardData, setDashboardData] = useState(null);
  const [etfs, setEtfs] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [selectedSector, setSelectedSector] = useState("");
  const [marketScore, setMarketScore] = useState(null);
  const [swingLeaders, setSwingLeaders] = useState([]);
  
  // Enhanced features
  const [chartData, setChartData] = useState({});
  const [selectedTimeframe, setSelectedTimeframe] = useState('1m');
  const [watchlists, setWatchlists] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [showFormulas, setShowFormulas] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  
  // Check authentication on app load
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
      } catch (err) {
        console.error('Invalid user data:', err);
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  // Fetch data when user is authenticated
  useEffect(() => {
    if (user) {
      fetchInitialData();
      // Set up periodic data refresh
      const interval = setInterval(fetchInitialData, 30000); // Every 30 seconds
      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchInitialData = async () => {
    try {
      await Promise.all([
        fetchDashboardData(),
        fetchETFs(),
        fetchSectors(),
        fetchMarketScore(),
        fetchSwingLeaders(),
        fetchWatchlists(),
        fetchChartData()
      ]);
    } catch (err) {
      console.error('Failed to fetch initial data:', err);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const response = await api.get('/api/dashboard');
      setDashboardData(response.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    }
  };

  const fetchETFs = async () => {
    try {
      const response = await api.get('/api/etfs?limit=200');
      setEtfs(response.data);
    } catch (err) {
      console.error('Failed to fetch ETFs:', err);
    }
  };

  const fetchSectors = async () => {
    try {
      const response = await api.get('/api/etfs/sectors');
      setSectors(response.data.sectors);
    } catch (err) {
      console.error('Failed to fetch sectors:', err);
    }
  };

  const fetchMarketScore = async () => {
    try {
      const response = await api.get('/api/market-score');
      setMarketScore(response.data);
    } catch (err) {
      console.error('Failed to fetch market score:', err);
    }
  };

  const fetchSwingLeaders = async () => {
    try {
      const response = await api.get('/api/etfs/swing-leaders');
      setSwingLeaders(response.data);
    } catch (err) {
      console.error('Failed to fetch swing leaders:', err);
    }
  };

  const fetchWatchlists = async () => {
    try {
      const response = await api.get('/api/watchlists/custom');
      setWatchlists(response.data);
    } catch (err) {
      console.error('Failed to fetch watchlists:', err);
    }
  };

  const fetchChartData = async (timeframe = '1m') => {
    try {
      const response = await api.get(`/api/charts/indices?timeframe=${timeframe}`);
      setChartData(response.data.data);
    } catch (err) {
      console.error('Failed to fetch chart data:', err);
    }
  };

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    setUser(null);
    setActiveTab('dashboard');
  };

  const analyzeChart = async (ticker) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/charts/${ticker}/analysis`);
      setSelectedStock(response.data);
      setActiveTab('ai-analysis');
    } catch (err) {
      alert('Failed to analyze chart. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const addToWatchlist = async (ticker, name, listName = 'Default') => {
    try {
      const watchlistItem = {
        ticker: ticker,
        name: name,
        list_name: listName,
        notes: '',
        priority: 1
      };
      
      await api.post(`/api/watchlists/custom/${listName}/add-stock`, watchlistItem);
      await fetchWatchlists(); // Refresh watchlists
      alert(`Added ${ticker} to ${listName} watchlist!`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add to watchlist');
    }
  };

  const exportToGoogleSheets = async () => {
    setExportLoading(true);
    try {
      const response = await api.get('/api/export/etfs');
      
      // Convert to CSV format
      const csvData = response.data.data;
      const headers = Object.keys(csvData[0]).join(',');
      const rows = csvData.map(row => Object.values(row).join(',')).join('\n');
      const csvContent = headers + '\n' + rows;
      
      // Download CSV file
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `etf-data-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      alert('ETF data exported successfully!');
    } catch (err) {
      alert('Failed to export data. Please try again.');
    } finally {
      setExportLoading(false);
    }
  };

  const updateETFData = async () => {
    try {
      setLoading(true);
      await api.post('/api/etfs/update');
      await fetchETFs();
      alert('ETF data updated successfully!');
    } catch (err) {
      alert('Failed to update ETF data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Utility functions
  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-400';
    if (change < 0) return 'text-red-400';
    return 'text-gray-400';
  };

  const getScoreColor = (score) => {
    if (score >= 28) return 'bg-green-600';
    if (score >= 20) return 'bg-yellow-600';
    return 'bg-red-600';
  };

  const getRSBadge = (rs) => {
    if (rs > 0.1) return <span className="bg-green-600 text-white px-2 py-1 rounded-full text-xs font-bold">Y</span>;
    if (rs > 0.02) return <span className="bg-yellow-600 text-white px-2 py-1 rounded-full text-xs font-bold">M</span>;
    return <span className="bg-red-600 text-white px-2 py-1 rounded-full text-xs font-bold">N</span>;
  };

  const getSwingDaysColor = (days) => {
    if (days <= 5) return 'text-green-400';
    if (days <= 15) return 'text-yellow-400';
    return 'text-red-400';
  };

  const filteredEtfs = useMemo(() => {
    return selectedSector ? etfs.filter(etf => etf.sector === selectedSector) : etfs;
  }, [etfs, selectedSector]);

  // Show loading spinner while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <FaSpinner className="animate-spin text-4xl text-blue-400 mx-auto mb-4" />
          <p className="text-gray-400">Loading ETF Intelligence System...</p>
        </div>
      </div>
    );
  }

  // Show login form if not authenticated
  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Top Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-8">
            <h1 className="text-2xl font-bold text-blue-400">ETF Intelligence Engine</h1>
            <div className="flex space-x-1">
              {[
                { id: "dashboard", label: "🏠 Dashboard", icon: FaChartLine },
                { id: "swing-grid", label: "📊 Analysis Grid", icon: FaTable },
                { id: "ai-analysis", label: "🧠 AI Assistant", icon: FaRobot },
                { id: "spreadsheet", label: "📋 Spreadsheet", icon: FaTable },
                { id: "ai-chat", label: "💬 AI Chat", icon: FaRobot }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeTab === tab.id
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:text-white hover:bg-gray-700"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setShowSettings(true)}
              className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-gray-700"
              title="Settings"
            >
              <FaCog className="text-lg" />
            </button>
            <button
              onClick={handleLogout}
              className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-gray-700"
              title="Logout"
            >
              <FaSignOutAlt className="text-lg" />
            </button>
            <div className="text-sm text-gray-400">
              Welcome, {user.email}
            </div>
          </div>
        </div>
      </nav>

      {/* Settings Modal */}
      <SettingsModal 
        isOpen={showSettings} 
        onClose={() => setShowSettings(false)} 
        user={user} 
      />

      {/* Main Content */}
      <main className="p-6">
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Dashboard Header with SA Greetings */}
            {dashboardData && (
              <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <h1 className="text-4xl font-bold mb-2">{dashboardData.greeting}</h1>
                    <p className="text-gray-400">Your Personal Trading Command Center</p>
                  </div>
                  
                  <div className="text-center">
                    <div className="bg-gray-700 rounded-lg p-4 mb-2">
                      <div className="flex items-center justify-center gap-2 text-lg font-semibold">
                        {dashboardData.sa_time.flag} {dashboardData.sa_time.time}
                      </div>
                      <div className="text-sm text-gray-400">{dashboardData.sa_time.date}</div>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <div className="bg-gray-700 rounded-lg p-4 mb-2">
                      <div className="flex items-center justify-center gap-2 text-lg font-semibold">
                        {dashboardData.ny_time.flag} {dashboardData.ny_time.time}
                      </div>
                      <div className="text-sm text-gray-400">Market opens in: {dashboardData.market_countdown}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Major Indices with Interactive Charts */}
            <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">📈 Major Market Indices</h2>
                <div className="flex gap-2">
                  {['1d', '1w', '1m', '1y', '5y'].map((timeframe) => (
                    <button
                      key={timeframe}
                      onClick={() => {
                        setSelectedTimeframe(timeframe);
                        fetchChartData(timeframe);
                      }}
                      className={`px-3 py-1 rounded-lg text-sm ${
                        selectedTimeframe === timeframe 
                          ? 'bg-blue-600 text-white' 
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {timeframe.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {['SPY', 'QQQ', 'DIA', 'IWM'].map((index) => (
                  <div key={index} className="bg-gray-700 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h3 className="font-semibold text-blue-300">{index}</h3>
                      {dashboardData?.major_indices[index] && (
                        <span className={`font-bold ${getChangeColor(dashboardData.major_indices[index].change_1d)}`}>
                          {dashboardData.major_indices[index].change_1d > 0 ? '+' : ''}{dashboardData.major_indices[index].change_1d.toFixed(2)}%
                        </span>
                      )}
                    </div>
                    {chartData[index] && (
                      <IndexChart data={chartData[index]} title={index} timeframe={selectedTimeframe} />
                    )}
                    {dashboardData?.major_indices[index] && (
                      <div className="text-sm text-gray-400 mt-2">
                        ${dashboardData.major_indices[index].price.toFixed(2)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Enhanced Market Score Card with Editable Formulas */}
            {marketScore && (
              <div className="bg-gray-800 rounded-xl p-6 shadow-lg">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-2xl font-bold">🎯 Market Situational Awareness Engine (MSAE)</h2>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => setShowFormulas(!showFormulas)}
                      className="bg-gray-600 hover:bg-gray-700 px-3 py-2 rounded text-sm"
                    >
                      ⚙️ {showFormulas ? 'Hide' : 'Show'} Formulas
                    </button>
                    <button 
                      onClick={exportToGoogleSheets}
                      disabled={exportLoading}
                      className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm disabled:opacity-50"
                    >
                      {exportLoading ? 'Exporting...' : '📊 Export to CSV'}
                    </button>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className={`text-5xl font-bold p-6 rounded-xl text-white ${getScoreColor(marketScore.total_score)}`}>
                      {marketScore.total_score}/40
                    </div>
                    <p className="text-2xl font-semibold mt-3">{marketScore.classification}</p>
                  </div>
                  
                  <div className="md:col-span-2">
                    <h3 className="text-lg font-semibold mb-2">🎯 Current Recommendation:</h3>
                    <p className="text-gray-300 mb-4 text-lg">{marketScore.recommendation}</p>
                    
                    <div className="grid grid-cols-4 gap-3 text-sm">
                      {[
                        { label: 'SATA Score', value: marketScore.sata_score, color: 'text-blue-400' },
                        { label: 'ADX Trend', value: marketScore.adx_score, color: 'text-green-400' },
                        { label: 'VIX Fear', value: marketScore.vix_score, color: 'text-red-400' },
                        { label: 'ATR Vol', value: marketScore.atr_score, color: 'text-yellow-400' },
                        { label: 'GMI Index', value: marketScore.gmi_score, color: 'text-purple-400' },
                        { label: 'NH-NL', value: marketScore.nhnl_score, color: 'text-indigo-400' },
                        { label: 'F&G Index', value: marketScore.fg_index_score, color: 'text-pink-400' },
                        { label: 'QQQ ATH', value: marketScore.qqq_ath_distance_score, color: 'text-cyan-400' }
                      ].map((metric, index) => (
                        <div key={index} className="bg-gray-700 p-3 rounded-lg text-center">
                          <div className="text-gray-400 text-xs">{metric.label}</div>
                          <div className={`text-lg font-bold ${metric.color}`}>{metric.value}/5</div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Formula Display Section */}
                {showFormulas && (
                  <div className="mt-6 pt-4 border-t border-gray-700">
                    <div className="bg-gray-900 p-4 rounded-lg text-sm">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono">
                        <div>
                          <div className="text-blue-400 font-semibold">SATA Score Formula:</div>
                          <div className="text-gray-300">Performance(40%) + RelStrength(30%) + Volume(20%) + Volatility(10%)</div>
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
                  </div>
                )}
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
                    <div className="flex flex-col gap-1 mt-2">
                      <button
                        onClick={() => analyzeChart(etf.ticker)}
                        className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-xs"
                      >
                        📈 Analyze
                      </button>
                      <button
                        onClick={() => addToWatchlist(etf.ticker, etf.name, 'Leaders')}
                        className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded text-xs"
                      >
                        ➕ Watch
                      </button>
                    </div>
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
                    {swingLeaders.filter(etf => 
                      ['TQQQ', 'FFTY', 'MGK', 'QQQ', 'SPXL'].includes(etf.ticker) && etf.change_1d > 0
                    ).map(etf => (
                      <div key={etf.ticker} className="flex justify-between bg-green-900 bg-opacity-30 p-2 rounded">
                        <span className="font-semibold">{etf.ticker}</span>
                        <span className="text-green-400">+{etf.change_1d?.toFixed(2)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold text-red-400 mb-3">🔴 Risk-Off Signals</h3>
                  <div className="space-y-2">
                    {swingLeaders.filter(etf => 
                      ['SQQQ', 'VIX', 'TLT', 'GLD'].includes(etf.ticker) && etf.change_1d > 0
                    ).map(etf => (
                      <div key={etf.ticker} className="flex justify-between bg-red-900 bg-opacity-30 p-2 rounded">
                        <span className="font-semibold">{etf.ticker}</span>
                        <span className="text-red-400">+{etf.change_1d?.toFixed(2)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Update Data Button */}
            <div className="text-center">
              <button
                onClick={updateETFData}
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 px-6 py-3 rounded-lg font-medium"
              >
                {loading ? 'Updating...' : '🔄 Update Market Data'}
              </button>
            </div>
          </div>
        )}

        {activeTab === "ai-chat" && <AIChat user={user} />}

        {activeTab === "swing-grid" && (
          <SwingAnalysisGrid
            etfs={etfs}
            sectors={sectors}
            selectedSector={selectedSector}
            setSelectedSector={setSelectedSector}
            analyzeChart={analyzeChart}
            addToWatchlist={addToWatchlist}
            showFormulas={showFormulas}
            setShowFormulas={setShowFormulas}
            exportToGoogleSheets={exportToGoogleSheets}
            exportLoading={exportLoading}
            updateETFData={updateETFData}
            loading={loading}
          />
        )}

        {activeTab === "ai-analysis" && (
          <AIAnalysisTab
            api={api}
            addToWatchlist={addToWatchlist}
          />
        )}

        {activeTab === "spreadsheet" && (
          <SpreadsheetTab
            api={api}
            etfs={etfs}
            sectors={sectors}
            selectedSector={selectedSector}
            setSelectedSector={setSelectedSector}
            exportLoading={exportLoading}
            setExportLoading={setExportLoading}
          />
        )}

        {/* Show message only if none of the implemented tabs are selected */}
        {!["dashboard", "ai-chat", "swing-grid", "ai-analysis", "spreadsheet"].includes(activeTab) && (
          <div className="bg-gray-800 rounded-xl p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">🚧 Feature Coming Soon</h2>
            <p className="text-gray-400">
              This feature is being developed. Please check back soon!
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;