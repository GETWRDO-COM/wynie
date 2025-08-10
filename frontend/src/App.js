import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { FaEye, FaEyeSlash, FaCog, FaSignOutAlt, FaLock, FaUser, FaRobot, FaChartLine, FaTable, FaTrademark, FaSpinner } from 'react-icons/fa';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import SwingAnalysisGrid from './components/SwingAnalysisGrid';
import AIAnalysisTab from './components/AIAnalysisTab';
import SpreadsheetTab from './components/SpreadsheetTab';
import ThemeWrapper from './components/ThemeWrapper';
import NavBar from './components/NavBar';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const api = axios.create({ baseURL: BACKEND_URL });
api.interceptors.request.use((config) => { const token = localStorage.getItem('authToken'); if (token) config.headers.Authorization = `Bearer ${token}`; return config; }, (e) => Promise.reject(e));
api.interceptors.response.use((r) => r, (e) => { if (e.response?.status === 401) { localStorage.removeItem('authToken'); localStorage.removeItem('user'); window.location.reload(); } return Promise.reject(e); });

const LoginForm = ({ onLogin }) => {
  const [credentials, setCredentials] = useState({ email: 'beetge@mwebbiz.co.za', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const handleLogin = async (e) => { e.preventDefault(); setLoading(true); setError(''); try { const r = await api.post('/api/auth/login', credentials); const { access_token, user } = r.data; localStorage.setItem('authToken', access_token); localStorage.setItem('user', JSON.stringify(user)); onLogin(user); } catch (err) { setError(err.response?.data?.detail || 'Login failed. Please check your credentials.'); } finally { setLoading(false); } };
  const handleForgotPassword = async () => { if (!credentials.email) { setError('Please enter your email address first.'); return; } try { const r = await api.post('/api/auth/forgot-password', { email: credentials.email }); alert(r.data.message + '\n\n' + (r.data.temp_instructions || '')); } catch { setError('Failed to send password reset instructions.'); } };
  return (
    <ThemeWrapper>
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="glass-panel glow-ring p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 glow-ring" style={{ background: 'linear-gradient(135deg, var(--brand-start), var(--brand-end))' }}>
              <FaLock className="text-2xl text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2 neon-text">HUNT BY WRDO</h1>
            <p className="text-gray-300">Secure Access Portal</p>
          </div>
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2"><FaUser className="inline mr-2" />Email Address</label>
              <input type="email" value={credentials.email} onChange={(e) => setCredentials({ ...credentials, email: e.target.value })} className="w-full form-input text-base" placeholder="Enter your email" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2"><FaLock className="inline mr-2" />Password</label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} value={credentials.password} onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} className="w-full form-input pr-12 text-base" placeholder="Enter your password" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white">{showPassword ? <FaEyeSlash /> : <FaEye />}</button>
              </div>
            </div>
            {error && (<div className="bg-red-900/60 border border-red-700 rounded-lg p-3 text-red-300 text-sm">{error}</div>)}
            <button type="submit" disabled={loading} className="w-full btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center">{loading ? (<><FaSpinner className="animate-spin mr-2" />Signing In...</>) : ('Sign In')}</button>
            <div className="text-center"><button type="button" onClick={handleForgotPassword} className="text-blue-400 hover:text-blue-300 text-sm underline">Forgot Password?</button></div>
          </form>
        </div>
      </div>
    </ThemeWrapper>
  );
};

const SettingsModal = ({ isOpen, onClose, user }) => { const [passwordData, setPasswordData] = useState({ current_password: '', new_password: '', confirm_password: '' }); const [loading, setLoading] = useState(false); const [message, setMessage] = useState(''); const [error, setError] = useState(''); const handleUpdatePassword = async (e) => { e.preventDefault(); if (passwordData.new_password !== passwordData.confirm_password) { setError('New passwords do not match.'); return; } setLoading(true); setError(''); setMessage(''); try { await api.post('/api/auth/settings', { current_password: passwordData.current_password, new_password: passwordData.new_password }); setMessage('Password updated successfully!'); setPasswordData({ current_password: '', new_password: '', confirm_password: '' }); } catch (err) { setError(err.response?.data?.detail || 'Failed to update password.'); } finally { setLoading(false); } }; if (!isOpen) return null; return (<div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"><div className="glass-card p-6 w-full max-w-md mx-4"><div className="flex justify-between items-center mb-4"><h2 className="text-xl font-bold text-white flex items-center">Settings</h2><button onClick={onClose} className="text-gray-400 hover:text-white text-xl">×</button></div><div className="mb-4 p-3 bg-white/5 rounded-lg"><p className="text-gray-300 text-sm">Account: {user?.email}</p><p className="text-gray-400 text-xs">Last Login: {user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}</p></div><form onSubmit={handleUpdatePassword} className="space-y-4"><h3 className="text-lg font-semibold text-white">Change Password</h3><input type="password" placeholder="Current Password" value={passwordData.current_password} onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })} className="w-full form-input" required /><input type="password" placeholder="New Password" value={passwordData.new_password} onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })} className="w-full form-input" required /><input type="password" placeholder="Confirm New Password" value={passwordData.confirm_password} onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })} className="w-full form-input" required />{error && <div className="text-red-400 text-sm">{error}</div>}{message && <div className="text-green-400 text-sm">{message}</div>}<button type="submit" disabled={loading} className="w-full btn btn-primary disabled:opacity-50">{loading ? 'Updating...' : 'Update Password'}</button></form></div></div>); };

const IndexChart = ({ data, title, timeframe }) => { const chartData = { labels: data?.dates || [], datasets: [{ label: title, data: data?.prices || [], borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59, 130, 246, 0.1)', borderWidth: 2, fill: true, tension: 0.1 }] }; const options = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, title: { display: false } }, scales: { x: { display: false, grid: { color: 'rgba(75, 85, 99, 0.3)' } }, y: { display: true, grid: { color: 'rgba(75, 85, 99, 0.3)' }, ticks: { color: 'rgb(156, 163, 175)', font: { size: 10 } } } } }; return (<div className="h-32"><Line data={chartData} options={options} /></div>); };

function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [etfs, setEtfs] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [selectedSector, setSelectedSector] = useState('');
  const [marketScore, setMarketScore] = useState(null);
  const [swingLeaders, setSwingLeaders] = useState([]);
  const [chartData, setChartData] = useState({});
  const [selectedTimeframe, setSelectedTimeframe] = useState('1m');
  const [watchlists, setWatchlists] = useState([]);
  const [selectedStock, setSelectedStock] = useState(null);
  const [showFormulas, setShowFormulas] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);

  useEffect(() => { const token = localStorage.getItem('authToken'); const userData = localStorage.getItem('user'); if (token && userData) { try { setUser(JSON.parse(userData)); } catch { localStorage.removeItem('authToken'); localStorage.removeItem('user'); } } setLoading(false); }, []);
  useEffect(() => { if (user) { fetchInitialData(); const i = setInterval(fetchInitialData, 30000); return () => clearInterval(i); } }, [user]);

  const fetchInitialData = async () => { try { await Promise.all([fetchDashboardData(), fetchETFs(), fetchSectors(), fetchMarketScore(), fetchSwingLeaders(), fetchWatchlists(), fetchChartData()]); } catch (e) { console.error('Failed to fetch initial data:', e); } };
  const fetchDashboardData = async () => { try { const r = await api.get('/api/dashboard'); setDashboardData(r.data); } catch (e) { console.error('Failed to fetch dashboard data:', e); } };
  const fetchETFs = async () => { try { const r = await api.get('/api/etfs?limit=200'); setEtfs(r.data); } catch (e) { console.error('Failed to fetch ETFs:', e); } };
  const fetchSectors = async () => { try { const r = await api.get('/api/etfs/sectors'); setSectors(r.data.sectors); } catch (e) { console.error('Failed to fetch sectors:', e); } };
  const fetchMarketScore = async () => { try { const r = await api.get('/api/market-score'); setMarketScore(r.data); } catch (e) { console.error('Failed to fetch market score:', e); } };
  const fetchSwingLeaders = async () => { try { const r = await api.get('/api/etfs/swing-leaders'); setSwingLeaders(r.data); } catch (e) { console.error('Failed to fetch swing leaders:', e); } };
  const fetchWatchlists = async () => { try { const r = await api.get('/api/watchlists/custom'); setWatchlists(r.data); } catch (e) { console.error('Failed to fetch watchlists:', e); } };
  const fetchChartData = async (timeframe = '1m') => { try { const r = await api.get(`/api/charts/indices?timeframe=${timeframe}`); setChartData(r.data.data); } catch (e) { console.error('Failed to fetch chart data:', e); } };

  const handleLogin = (u) => setUser(u);
  const handleLogout = () => { localStorage.removeItem('authToken'); localStorage.removeItem('user'); setUser(null); setActiveTab('dashboard'); };

  if (loading) return (<ThemeWrapper><div className="min-h-screen flex items-center justify-center"><div className="text-center"><FaSpinner className="animate-spin text-4xl text-blue-400 mx-auto mb-4" /><p className="text-gray-300">Loading HUNT BY WRDO...</p></div></div></ThemeWrapper>);
  if (!user) return <LoginForm onLogin={handleLogin} />;

  return (
    <ThemeWrapper>
      <NavBar activeTab={activeTab} setActiveTab={setActiveTab} user={user} onSettings={() => setShowSettings(true)} onLogout={handleLogout} />
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} user={user} />
      <main className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {dashboardData && (
              <div className="glass-card p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <h1 className="text-4xl font-bold mb-2">{dashboardData.greeting}</h1>
                    <p className="text-gray-300">Welcome to HUNT BY WRDO</p>
                  </div>
                  <div className="text-center"><div className="glass-panel rounded-lg p-4 mb-2"><div className="text-gray-300">South Africa 🇿🇦 / United States 🇺🇸</div><div className="text-xs text-gray-400">Dual timezone display</div></div></div>
                  <div className="text-center"><div className="glass-panel rounded-lg p-4 mb-2"><div className="text-gray-300">Market Status</div><div className="text-xs text-gray-400">NYSE countdown &amp; overview</div></div></div>
                </div>
              </div>
            )}
          </div>
        )}
        {activeTab === 'swing-grid' && (<div className="glass-card p-6"><SwingAnalysisGrid api={api} etfs={selectedSector ? etfs.filter(e => e.sector === selectedSector) : etfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} analyzeChart={() => {}} addToWatchlist={() => {}} /></div>)}
        {activeTab === 'ai-analysis' && (<div className="space-y-6"><AIAnalysisTab api={api} addToWatchlist={() => {}} /></div>)}
        {activeTab === 'spreadsheet' && (<div className="glass-card p-6"><SpreadsheetTab api={api} etfs={etfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} exportLoading={exportLoading} setExportLoading={setExportLoading} /></div>)}
        {activeTab === 'ai-chat' && (<AIChat user={user} />)}
      </main>
    </ThemeWrapper>
  );
}

export default App;