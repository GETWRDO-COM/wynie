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
import ThemeWrapper from './components/ThemeWrapper';

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
    <ThemeWrapper>
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="glass-panel glow-ring p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="bg-gradient-to-tr from-blue-600 to-purple-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 glow-ring">
              <FaLock className="text-2xl text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2 neon-text">ETF Intelligence</h1>
            <p className="text-gray-300">Secure Access Portal</p>
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
                className="w-full form-input text-base"
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
                  className="w-full form-input pr-12 text-base"
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-900/60 border border-red-700 rounded-lg p-3 text-red-300 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
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
    </ThemeWrapper>
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
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="glass-card p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-white flex items-center">
            <FaCog className="mr-2" />
            Settings
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button>
        </div>

        <div className="mb-4 p-3 bg-white/5 rounded-lg">
          <p className="text-gray-300 text-sm">Account: {user?.email}</p>
          <p className="text-gray-400 text-xs">Last Login: {user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}</p>
        </div>

        <form onSubmit={handleUpdatePassword} className="space-y-4">
          <h3 className="text-lg font-semibold text-white">Change Password</h3>
          <input type="password" placeholder="Current Password" value={passwordData.current_password} onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })} className="w-full form-input" required />
          <input type="password" placeholder="New Password" value={passwordData.new_password} onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })} className="w-full form-input" required />
          <input type="password" placeholder="Confirm New Password" value={passwordData.confirm_password} onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })} className="w-full form-input" required />
          {error && <div className="text-red-400 text-sm">{error}</div>}
          {message && <div className="text-green-400 text-sm">{message}</div>}
          <button type="submit" disabled={loading} className="w-full btn btn-primary disabled:opacity-50">{loading ? 'Updating...' : 'Update Password'}</button>
        </form>
      </div>
    </div>
  );
};

// AI Chat Component (unchanged UI except styles rely on new classes)
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
      const sessionData = { title: 'New Trading Chat', model: selectedModel };
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
    const userMessage = { role: 'user', content: inputMessage, timestamp: new Date().toISOString() };
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
      const aiMessage = { role: 'assistant', content: response.data.response, timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, aiMessage]);
      setInputMessage('');
    } catch (err) {
      const errorMessage = { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', timestamp: new Date().toISOString() };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 h-[600px] flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <FaRobot className="mr-2 text-blue-400" />
          AI Trading Assistant
        </h2>
        <div className="flex gap-2">
          <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)} className="form-select text-sm">
            {Object.entries(availableModels).map(([key, model]) => (
              <option key={key} value={key}>{key === 'latest' ? `🚀 Latest (${model})` : `${key}`}</option>
            ))}
          </select>
          <button onClick={createNewSession} className="btn btn-secondary">New Chat</button>
        </div>
      </div>

      {/* Chart Context Controls */}
      <div className="mb-4 p-3 bg-white/5 rounded-lg">
        <div className="flex items-center gap-4">
          <label className="flex items-center text-sm text-gray-300">
            <input type="checkbox" checked={includeChart} onChange={(e) => setIncludeChart(e.target.checked)} className="mr-2" />
            Include Chart Analysis
          </label>
          {includeChart && (
            <input type="text" placeholder="Enter ticker (e.g., AAPL, SPY)" value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} className="px-3 py-1 bg-gray-700 border border-white/10 rounded text-white text-sm" />
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
          <div key={index} className={`p-3 rounded-lg ${message.role === 'user' ? 'bg-blue-600/90 ml-12 text-white glow-ring' : 'bg-white/5 mr-12 text-gray-100'}`}>
            <div className="text-sm opacity-75 mb-1">{message.role === 'user' ? 'You' : `AI (${selectedModel})`}</div>
            <div className="whitespace-pre-wrap">{message.content}</div>
          </div>
        ))}
        {loading && (
          <div className="bg-white/5 mr-12 p-3 rounded-lg">
            <div className="flex items-center text-gray-300">
              <FaSpinner className="animate-spin mr-2" />
              AI is thinking...
            </div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={sendMessage} className="flex gap-2">
        <input type="text" value={inputMessage} onChange={(e) => setInputMessage(e.target.value)} placeholder={includeChart && ticker ? `Ask about ${ticker} chart...` : "Ask me about trading, markets, or analysis..."} className="flex-1 form-input" disabled={loading} />
        <button type="submit" disabled={loading || !inputMessage.trim()} className="btn btn-primary disabled:opacity-50">Send</button>
      </form>
    </div>
  );
};

// Chart Component for Indices
const IndexChart = ({ data, title, timeframe }) => {
  const chartData = { labels: data?.dates || [], datasets: [{ label: title, data: data?.prices || [], borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', borderWidth: 2, fill: true, tension: 0.1 }] };
  const options = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, title: { display: false } }, scales: { x: { display: false, grid: { color: 'rgba(75, 85, 99, 0.3)' } }, y: { display: true, grid: { color: 'rgba(75, 85, 99, 0.3)' }, ticks: { color: 'rgb(156, 163, 175)', font: { size: 10 } } } } };
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
      const interval = setInterval(fetchInitialData, 30000);
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

  const fetchDashboardData = async () => { try { const response = await api.get('/api/dashboard'); setDashboardData(response.data); } catch (err) { console.error('Failed to fetch dashboard data:', err); } };
  const fetchETFs = async () => { try { const response = await api.get('/api/etfs?limit=200'); setEtfs(response.data); } catch (err) { console.error('Failed to fetch ETFs:', err); } };
  const fetchSectors = async () => { try { const response = await api.get('/api/etfs/sectors'); setSectors(response.data.sectors); } catch (err) { console.error('Failed to fetch sectors:', err); } };
  const fetchMarketScore = async () => { try { const response = await api.get('/api/market-score'); setMarketScore(response.data); } catch (err) { console.error('Failed to fetch market score:', err); } };
  const fetchSwingLeaders = async () => { try { const response = await api.get('/api/etfs/swing-leaders'); setSwingLeaders(response.data); } catch (err) { console.error('Failed to fetch swing leaders:', err); } };
  const fetchWatchlists = async () => { try { const response = await api.get('/api/watchlists/custom'); setWatchlists(response.data); } catch (err) { console.error('Failed to fetch watchlists:', err); } };
  const fetchChartData = async (timeframe = '1m') => { try { const response = await api.get(`/api/charts/indices?timeframe=${timeframe}`); setChartData(response.data.data); } catch (err) { console.error('Failed to fetch chart data:', err); } };

  const handleLogin = (userData) => { setUser(userData); };
  const handleLogout = () => { localStorage.removeItem('authToken'); localStorage.removeItem('user'); setUser(null); setActiveTab('dashboard'); };

  // Utility helpers
  const filteredEtfs = useMemo(() => { return selectedSector ? etfs.filter(etf => etf.sector === selectedSector) : etfs; }, [etfs, selectedSector]);

  if (loading) {
    return (
      <ThemeWrapper>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <FaSpinner className="animate-spin text-4xl text-blue-400 mx-auto mb-4" />
            <p className="text-gray-300">Loading ETF Intelligence System...</p>
          </div>
        </div>
      </ThemeWrapper>
    );
  }

  if (!user) { return <LoginForm onLogin={handleLogin} />; }

  return (
    <ThemeWrapper>
      {/* Top Navigation */}
      <nav className="nav-shell px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <div className="flex items-center gap-3">
              <img src="/assets/theme/logo.svg" alt="logo" className="w-7 h-7" />
              <h1 className="text-xl sm:text-2xl font-bold neon-text">ETF Intelligence Engine</h1>
            </div>
            <div className="hidden md:flex items-center">
              <div className="nav-tabs flex items-center gap-1">
                {[
                  { id: "dashboard", label: "🏠 Dashboard" },
                  { id: "swing-grid", label: "📊 Analysis Grid" },
                  { id: "ai-analysis", label: "🧠 AI Assistant" },
                  { id: "spreadsheet", label: "📋 Spreadsheet" },
                  { id: "ai-chat", label: "💬 AI Chat" }
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`nav-tab ${activeTab === tab.id ? 'active' : 'inactive'}`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button onClick={() => setShowSettings(true)} className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" title="Settings">
              <FaCog className="text-lg" />
            </button>
            <button onClick={handleLogout} className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" title="Logout">
              <FaSignOutAlt className="text-lg" />
            </button>
            <div className="hidden sm:block text-sm text-gray-400">Welcome, {user.email}</div>
          </div>
        </div>
      </nav>

      {/* Settings Modal */}
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} user={user} />

      {/* Main Content */}
      <main className="p-6 space-y-6">
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Dashboard Header with SA Greetings */}
            {dashboardData && (
              <div className="glass-card p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <h1 className="text-4xl font-bold mb-2">{dashboardData.greeting}</h1>
                    <p className="text-gray-300">Your Personal Trading Command Center</p>
                  </div>
                  <div className="text-center">
                    <div className="glass-panel rounded-lg p-4 mb-2">
                      <div className="text-gray-300">South Africa 🇿🇦 / United States 🇺🇸</div>
                      <div className="text-xs text-gray-400">Dual timezone display</div>
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="glass-panel rounded-lg p-4 mb-2">
                      <div className="text-gray-300">Market Status</div>
                      <div className="text-xs text-gray-400">NYSE countdown &amp; overview</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "swing-grid" && (
          <div className="glass-card p-6">
            <SwingAnalysisGrid api={api} etfs={filteredEtfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} analyzeChart={(ticker) => setActiveTab('ai-analysis')} addToWatchlist={() => {}} />
          </div>
        )}

        {activeTab === "ai-analysis" && (
          <div className="space-y-6">
            <AIAnalysisTab api={api} addToWatchlist={() => {}} />
          </div>
        )}

        {activeTab === "spreadsheet" && (
          <div className="glass-card p-6">
            <SpreadsheetTab api={api} etfs={etfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} exportLoading={exportLoading} setExportLoading={setExportLoading} />
          </div>
        )}

        {activeTab === "ai-chat" && (
          <AIChat user={user} />
        )}
      </main>
    </ThemeWrapper>
  );
}

export default App;