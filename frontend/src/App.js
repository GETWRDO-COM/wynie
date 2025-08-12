import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { FaEye, FaEyeSlash, FaCog, FaSignOutAlt, FaLock, FaUser, FaSpinner } from 'react-icons/fa';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import SwingAnalysisGrid from './components/SwingAnalysisGrid';
import AIAnalysisTab from './components/AIAnalysisTab';
import SpreadsheetTab from './components/SpreadsheetTab';
import ThemeWrapper from './components/ThemeWrapper';
import NavBar from './components/NavBar';
import AIChat from './components/AIChat';
import HeroBanner from './components/HeroBanner';
import NewsTicker from './components/NewsTicker';
import DashboardQuickSections from './components/DashboardQuickSections';
import MarketCharts from './components/MarketCharts';
import PolygonKeySettings from './components/PolygonKeySettings';
import GreedFearCard from './components/GreedFearCard';
import FloatingChat from './components/FloatingChat';
import MyPerformance from './components/MyPerformance';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
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
        <div className="glass-panel glow-ring p-8 w-full max-w-md animate-fade-in">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 glow-ring" style={{ background: 'linear-gradient(135deg, var(--brand-start), var(--brand-end))' }}>
              <FaLock className="text-2xl text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2 neon-text">HUNT by WRDO</h1>
            <p className="text-gray-300">Secure Access Portal</p>
          </div>
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2"><FaUser className="inline mr-2" />Email Address</label>
              <input type="email" value={credentials.email} onChange={(e) => setCredentials({ ...credentials, email: e.target.value })} className="w-full form-input text-base" placeholder="Enter your email" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
              <div className="relative">
                <input type={showPassword ? 'text' : 'password'} value={credentials.password} onChange={(e) => setCredentials({ ...credentials, password: e.target.value })} className="w-full form-input pr-12 text-base" placeholder="Enter your password" required />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-200 hover:text-white">{showPassword ? 'Hide' : 'Show'}</button>
              </div>
            </div>
            {error && (<div className="bg-red-900/60 border border-red-700 rounded-lg p-3 text-red-300 text-sm">{error}</div>)}
            <button type="submit" disabled={loading} className="w-full btn btn-primary-strong disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-base py-3">{loading ? (<><FaSpinner className="animate-spin mr-2" />Signing In...</>) : ('Sign In')}</button>
            <div className="text-center"><button type="button" onClick={handleForgotPassword} className="text-blue-400 hover:text-blue-300 text-sm underline">Forgot Password?</button></div>
          </form>
        </div>
      </div>
    </ThemeWrapper>
  );
};

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

  if (loading) return (<ThemeWrapper><div className="min-h-screen flex items-center justify-center"><div className="text-center"><FaSpinner className="animate-spin text-4xl text-blue-400 mx-auto mb-4" /><p className="text-gray-300">Loading HUNT by WRDO...</p></div></div></ThemeWrapper>);
  if (!user) return <LoginForm onLogin={handleLogin} />;

  return (
    <ThemeWrapper>
      <NavBar activeTab={activeTab} setActiveTab={setActiveTab} user={user} onSettings={() => setShowSettings(true)} onLogout={handleLogout} />
      <div className="animate-fade-in">
        <main className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto">
          {showSettings && (
            <div className="glass-panel p-4">
              <h2 className="text-white/90 font-semibold mb-3">Settings</h2>
              <div className="space-y-4">
                <div>
                  <h3 className="text-white/80 font-semibold mb-2">Integrations</h3>
                  <div className="space-y-3">
                    <div className="text-xs text-gray-400">Polygon.io</div>
                    <div>
                      <PolygonKeySettings />
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-3">
                <button onClick={() => setShowSettings(false)} className="btn">Close</button>
              </div>
            </div>
          )}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              <HeroBanner user={user} />
              <DashboardQuickSections chartData={chartData} swingLeaders={swingLeaders} watchlists={watchlists} marketScore={marketScore} />
              <GreedFearCard />
              <MarketCharts />
            </div>
          )}
          {activeTab === 'swing-grid' && (<div className="glass-panel p-6 animate-fade-in"><SwingAnalysisGrid api={api} etfs={selectedSector ? etfs.filter(e => e.sector === selectedSector) : etfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} analyzeChart={() => {}} addToWatchlist={() => {}} /></div>)}
          {activeTab === 'ai-analysis' && (<div className="space-y-6 animate-fade-in"><AIAnalysisTab api={api} addToWatchlist={() => {}} /></div>)}
          {activeTab === 'spreadsheet' && (<div className="glass-panel p-6 animate-fade-in"><SpreadsheetTab api={api} etfs={etfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} exportLoading={false} setExportLoading={() => {}} /></div>)}
          {activeTab === 'ai-chat' && (<div className="animate-fade-in"><AIChat api={api} user={user} /></div>)}
        </main>
      </div>
      <NewsTicker />
      <FloatingChat api={api} user={user} />
    </ThemeWrapper>
  );
}

export default App;