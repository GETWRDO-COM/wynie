import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { FaUser, FaSpinner } from 'react-icons/fa';
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
import MarketScoreCard from './components/MarketScoreCard';
import BackendStatus from './components/BackendStatus';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const api = axios.create({ baseURL: BACKEND_URL });
api.interceptors.request.use((config) =&gt; { const token = localStorage.getItem('authToken'); if (token) config.headers.Authorization = `Bearer ${token}`; return config; }, (e) =&gt; Promise.reject(e));
api.interceptors.response.use((r) =&gt; r, (e) =&gt; { if (e.response?.status === 401) { localStorage.removeItem('authToken'); localStorage.removeItem('user'); window.location.reload(); } return Promise.reject(e); });

const LoginForm = ({ onLogin }) =&gt; {
  const [credentials, setCredentials] = useState({ email: 'beetge@mwebbiz.co.za', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const handleLogin = async (e) =&gt; { e.preventDefault(); setLoading(true); setError(''); try { const r = await api.post('/api/auth/login', credentials); const { access_token, user } = r.data; localStorage.setItem('authToken', access_token); localStorage.setItem('user', JSON.stringify(user)); onLogin(user); } catch (err) { setError(err.response?.data?.detail || 'Login failed. Please check your credentials.'); } finally { setLoading(false); } };
  const handleForgotPassword = async () =&gt; { if (!credentials.email) { setError('Please enter your email address first.'); return; } try { const r = await api.post('/api/auth/forgot-password', { email: credentials.email }); alert(r.data.message + '\n\n' + (r.data.temp_instructions || '')); } catch { setError('Failed to send password reset instructions.'); } };
  return (
    <ThemeWrapper>
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="glass-panel glow-ring p-8 w-full max-w-md animate-fade-in">
          <div className="text-center mb-8">
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

  useEffect(() =&gt; { const token = localStorage.getItem('authToken'); const userData = localStorage.getItem('user'); if (token &amp;&amp; userData) { try { setUser(JSON.parse(userData)); } catch { localStorage.removeItem('authToken'); localStorage.removeItem('user'); } } setLoading(false); }, []);
  useEffect(() =&gt; { if (user) { fetchInitialData(); const i = setInterval(fetchInitialData, 30000); return () =&gt; clearInterval(i); } }, [user]);

  const fetchInitialData = async () =&gt; { try { await Promise.all([fetchDashboardData(), fetchETFs(), fetchSectors(), fetchMarketScore(), fetchSwingLeaders(), fetchWatchlists(), fetchChartData()]); } catch (e) { console.error('Failed to fetch initial data:', e); } };
  const fetchDashboardData = async () =&gt; { try { const r = await api.get('/api/dashboard'); setDashboardData(r.data); } catch (e) { console.error('Failed to fetch dashboard data:', e); } };
  const fetchETFs = async () =&gt; { try { const r = await api.get('/api/etfs?limit=200'); setEtfs(r.data); } catch (e) { console.error('Failed to fetch ETFs:', e); } };
  const fetchSectors = async () =&gt; { try { const r = await api.get('/api/etfs/sectors'); setSectors(r.data.sectors); } catch (e) { console.error('Failed to fetch sectors:', e); } };
  const fetchMarketScore = async () =&gt; { try { const r = await api.get('/api/market-score'); setMarketScore(r.data); } catch (e) { console.error('Failed to fetch market score:', e); } };
  const fetchSwingLeaders = async () =&gt; { try { const r = await api.get('/api/etfs/swing-leaders'); setSwingLeaders(r.data); } catch (e) { console.error('Failed to fetch swing leaders:', e); } };
  const fetchWatchlists = async () =&gt; { try { const r = await api.get('/api/watchlists/custom'); setWatchlists(r.data); } catch (e) { console.error('Failed to fetch watchlists:', e); } };
  const fetchChartData = async (timeframe = '1m') =&gt; { try { const r = await api.get(`/api/charts/indices?timeframe=${timeframe}`); setChartData(r.data.data); } catch (e) { console.error('Failed to fetch chart data:', e); } };

  const handleLogin = (u) =&gt; setUser(u);
  const handleLogout = () =&gt; { localStorage.removeItem('authToken'); localStorage.removeItem('user'); setUser(null); setActiveTab('dashboard'); };

  if (loading) return (&lt;ThemeWrapper&gt;&lt;div className="min-h-screen flex items-center justify-center"&gt;&lt;div className="text-center"&gt;&lt;FaSpinner className="animate-spin text-4xl text-blue-400 mx-auto mb-4" /&gt;&lt;p className="text-gray-300"&gt;Loading HUNT by WRDO...&lt;/p&gt;&lt;/div&gt;&lt;/div&gt;&lt;/ThemeWrapper&gt;);
  if (!user) return &lt;LoginForm onLogin={handleLogin} /&gt;;

  return (
    &lt;ThemeWrapper&gt;
      &lt;NavBar activeTab={activeTab} setActiveTab={setActiveTab} user={user} onSettings={() =&gt; setShowSettings(true)} onLogout={handleLogout} /&gt;
      &lt;div className="animate-fade-in"&gt;
        &lt;main className="p-4 sm:p-6 space-y-6 max-w-7xl mx-auto"&gt;
          {showSettings &amp;&amp; (
            &lt;div className="glass-panel p-4"&gt;
              &lt;h2 className="text-white/90 font-semibold mb-3"&gt;Settings&lt;/h2&gt;
              &lt;div className="space-y-4"&gt;
                &lt;div&gt;
                  &lt;h3 className="text-white/80 font-semibold mb-2"&gt;Integrations&lt;/h3&gt;
                  &lt;div className="space-y-3"&gt;
                    &lt;div className="text-xs text-gray-400"&gt;Polygon.io&lt;/div&gt;
                    &lt;div&gt;
                      &lt;PolygonKeySettings /&gt;
                    &lt;/div&gt;
                    &lt;BackendStatus /&gt;
                  &lt;/div&gt;
                &lt;/div&gt;
              &lt;/div&gt;
              &lt;div className="mt-3"&gt;
                &lt;button onClick={() =&gt; setShowSettings(false)} className="btn"&gt;Close&lt;/button&gt;
              &lt;/div&gt;
            &lt;/div&gt;
          )}
          {activeTab === 'dashboard' &amp;&amp; (
            &lt;div className="space-y-6"&gt;
              &lt;HeroBanner user={user} /&gt;
              &lt;MyPerformance api={api} /&gt;
              &lt;div className="grid grid-cols-1 lg:grid-cols-2 gap-3"&gt;
                &lt;GreedFearCard /&gt;
                &lt;MarketScoreCard marketScore={marketScore} /&gt;
              &lt;/div&gt;
              &lt;MarketCharts /&gt;
              &lt;DashboardQuickSections swingLeaders={swingLeaders} watchlists={watchlists} marketScore={marketScore} /&gt;
            &lt;/div&gt;
          )}
          {activeTab === 'swing-grid' &amp;&amp; (&lt;div className="glass-panel p-6 animate-fade-in"&gt;&lt;SwingAnalysisGrid api={api} etfs={selectedSector ? etfs.filter(e =&gt; e.sector === selectedSector) : etfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} analyzeChart={() =&gt; {}} addToWatchlist={() =&gt; {}} /&gt;&lt;/div&gt;)}
          {activeTab === 'ai-analysis' &amp;&amp; (&lt;div className="space-y-6 animate-fade-in"&gt;&lt;AIAnalysisTab api={api} addToWatchlist={() =&gt; {}} /&gt;&lt;/div&gt;)}
          {activeTab === 'spreadsheet' &amp;&amp; (&lt;div className="glass-panel p-6 animate-fade-in"&gt;&lt;SpreadsheetTab api={api} etfs={etfs} sectors={sectors} selectedSector={selectedSector} setSelectedSector={setSelectedSector} exportLoading={false} setExportLoading={() =&gt; {}} /&gt;&lt;/div&gt;)}
          {activeTab === 'ai-chat' &amp;&amp; (&lt;div className="animate-fade-in"&gt;&lt;AIChat api={api} user={user} /&gt;&lt;/div&gt;)}
        &lt;/main&gt;
      &lt;/div&gt;
      &lt;NewsTicker /&gt;
      &lt;FloatingChat api={api} user={user} /&gt;
    &lt;/ThemeWrapper&gt;
  );
}

export default App;