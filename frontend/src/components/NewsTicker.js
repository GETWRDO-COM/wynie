import React, { useEffect, useMemo, useState } from 'react';

const FEEDS = { All:'All', USA:'USA', World:'World', 'South Africa':'South Africa', 'Stock Market':'Stock Market', 'Finance News':'Finance News' };

const NewsTicker = () => {
  const [category, setCategory] = useState('All');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const cacheKey = (cat) => `ticker:${cat}`;

  const setCached = (cat, arr) => {
    try { localStorage.setItem(cacheKey(cat), JSON.stringify({ t: Date.now(), items: arr })); } catch {}
  };
  const getCached = (cat) => {
    try { const raw = localStorage.getItem(cacheKey(cat)); if (!raw) return null; const js = JSON.parse(raw); return js?.items || null; } catch { return null; }
  };

  const fetchFeed = async (cat) => {
    setLoading(true); setError('');
    try {
      const resp = await fetch(`${BACKEND_URL}/api/news?category=${encodeURIComponent(cat)}`);
      const data = await resp.json();
      const parsed = (data && data.items) ? data.items.slice(0, 80) : [];
      if (parsed.length === 0 && cat !== 'All') {
        // fallback to All feed
        await fetchFeed('All');
        return;
      }
      setItems(parsed);
      setCached(cat, parsed);
      if (!parsed.length) setError('No headlines available');
    } catch (e) {
      // fallback to cache, then All, then show error
      const cached = getCached(cat) || getCached('All');
      if (cached && cached.length) {
        setItems(cached);
      } else {
        setError('Cannot reach news service');
        setItems([]);
      }
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchFeed(category); const id = setInterval(() => fetchFeed(category), 180000); return () => clearInterval(id); }, [category]);

  const parts = useMemo(() => { const arr = loading ? ['Loading news…'] : items.length ? items.map((it) => it.title) : [error || 'No headlines available']; return [...arr, ...arr, ...arr, ...arr, ...arr, ...arr]; }, [items, loading, error]);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[5000]">
      <div className="mx-auto max-w-7xl">
        <div className="rounded-2xl flex items-center gap-4 px-4 py-2.5 mb-3" style={{ background: 'rgba(10,10,12,0.97)', border: '1px solid rgba(255,255,255,0.14)' }}>
          <div className="flex items-center gap-2 min-w-[280px] text-sm text-white">
            Breaking News
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="text-white text-xs py-0.5 px-2 rounded bg-black/80 border border-white/20">
              {Object.keys(FEEDS).map((k) => (<option key={k} value={k} className="bg-black text-white">{k}</option>))}
            </select>
            <button onClick={()=>fetchFeed(category)} className="btn btn-outline text-[10px] py-0.5 px-2">Reload</button>
          </div>
          <div className="relative flex-1 overflow-hidden h-8">
            <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-black/80 via-transparent to-black/80" />
            <div className="absolute whitespace-nowrap will-change-transform animate-[ticker_1200s_linear_infinite] text-base text-white">
              {(parts && parts.length) ? (
                parts.map((t, i) => (
                  <span key={i} className="inline-flex items-center">{i > 0 && <span className="mx-4 text-white/50">|</span>}{t}</span>
                ))
              ) : (
                <span className="inline-flex items-center">{loading ? 'Loading news…' : (error || 'No headlines available')}</span>
              )}
            </div>
          </div>
        </div>
      </div>
      <style>{`@keyframes ticker { 0% { transform: translateX(100%);} 100% { transform: translateX(-100%);} }`}</style>
    </div>
  );
};

export default NewsTicker;