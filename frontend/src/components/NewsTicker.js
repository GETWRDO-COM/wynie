import React, { useEffect, useMemo, useState } from 'react';

const FEEDS = {
  All: 'All',
  USA: 'USA',
  World: 'World',
  'South Africa': 'South Africa',
  'Stock Market': 'Stock Market',
  'Finance News': 'Finance News',
};

const NewsTicker = () => {
  const [category, setCategory] = useState('All');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = (typeof import !== 'undefined' && import.meta && import.meta.env && import.meta.env.REACT_APP_BACKEND_URL) || process.env.REACT_APP_BACKEND_URL || '';

  const fetchFeed = async (cat) => {
    setLoading(true);
    try {
      const resp = await fetch(`${BACKEND_URL}/api/news?category=${encodeURIComponent(cat)}`);
      const data = await resp.json();
      const parsed = (data && data.items) ? data.items.slice(0, 50) : [];
      setItems(parsed);
    } catch (e) {
      console.error('News load failed', e);
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeed(category);
    const id = setInterval(() => fetchFeed(category), 180000);
    return () => clearInterval(id);
  }, [category]);

  const parts = useMemo(() => {
    const arr = loading ? ['Loading news…'] : items.length ? items.map((it) => it.title) : ['No headlines available'];
    return [...arr, ...arr, ...arr, ...arr, ...arr, ...arr];
  }, [items, loading]);

  return (
    <div className="fixed bottom-0 left-0 right-0 z-[60]">
      <div className="mx-auto max-w-7xl">
        <div className="rounded-xl flex items-center gap-3 px-3 py-1.5 mb-3" style={{ background: 'rgba(0,0,0,0.75)', border: '1px solid rgba(255,255,255,0.1)' }}>
          <div className="flex items-center gap-2 min-w-[220px] text-xs text-white/90">
            Breaking News
            <select value={category} onChange={(e) => setCategory(e.target.value)} className="text-white text-xs py-0.5 px-2 rounded bg-black/80 border border-white/20">
              {Object.keys(FEEDS).map((k) => (
                <option key={k} value={k} className="bg-black text-white">{k}</option>
              ))}
            </select>
          </div>
          <div className="relative flex-1 overflow-hidden h-6">
            <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-black/80 via-transparent to-black/80" />
            <div className="absolute whitespace-nowrap will-change-transform animate-[ticker_900s_linear_infinite] text-xs text-white/90">
              {parts.map((t, i) => (
                <span key={i} className="inline-flex items-center">
                  {i > 0 && <span className="mx-4 text-white/40">|</span>}
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
      <style>{`@keyframes ticker { 0% { transform: translateX(100%);} 100% { transform: translateX(-100%);} }`}</style>
    </div>
  );
};

export default NewsTicker;