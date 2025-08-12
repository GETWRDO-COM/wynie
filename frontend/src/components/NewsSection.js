import React, { useEffect, useMemo, useState } from 'react';

const CATS = ['Watchlist','All','USA','South Africa','Stock Market','Finance News'];

const NewsSection = ({ api }) => {
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
  const [category, setCategory] = useState('Watchlist');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [wlTickers, setWlTickers] = useState([]);
  const [earnings, setEarnings] = useState([]);

  useEffect(() => {
    // load watchlists to build tickers
    (async () => {
      try {
        const r = await api.get('/api/watchlists/custom');
        const all = r.data || [];
        const symbols = new Set();
        all.forEach(wl => (wl.stocks||[]).forEach(s => { if (s?.symbol) symbols.add(s.symbol.toUpperCase()); }));
        const list = Array.from(symbols).slice(0, 20); // cap for query
        setWlTickers(list);
        if (list.length) {
          try {
            const er = await fetch(`${BACKEND_URL}/api/earnings?tickers=${encodeURIComponent(list.join(','))}`);
            const ej = await er.json();
            setEarnings(ej.items || []);
          } catch {}
        }
      } catch {}
    })();
  }, []);

  const fetchNews = async (cat) => {
    setLoading(true); setErr('');
    try {
      let url = `${BACKEND_URL}/api/news?category=${encodeURIComponent(cat)}`;
      if (cat === 'Watchlist') {
        if (!wlTickers.length) { setItems([]); setLoading(false); return; }
        const q = wlTickers.slice(0,6).join(' OR ');
        url = `${BACKEND_URL}/api/news?q=${encodeURIComponent(q)}`;
      }
      const resp = await fetch(url);
      const data = await resp.json();
      const parsed = (data && data.items) ? data.items.slice(0, 12) : [];
      setItems(parsed);
    } catch (e) {
      setErr('News unavailable'); setItems([]);
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchNews(category); }, [category, wlTickers.join(',')]);

  return (
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-white/90 font-semibold">Top Headlines</div>
        <div className="flex flex-wrap gap-2">
          {CATS.map(c => (
            <button key={c} onClick={() => setCategory(c)} className={`px-3 py-1.5 rounded-lg text-xs ${category===c?'text-white bg-white/10 border border-white/10':'text-gray-300 hover:text-white hover:bg-white/5'}`}>{c}</button>
          ))}
        </div>
      </div>
      {err && <div className="text-xs text-amber-300 mb-2">{err}</div>}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div>
          <ul className="space-y-2">
            {loading && <li className="text-gray-400 text-sm">Loading headlines…</li>}
            {!loading && items.map((it, idx) => (
              <li key={idx} className="text-sm">
                <a href={it.link} target="_blank" rel="noopener noreferrer" className="text-white/90 hover:text-white underline-offset-2 hover:underline">{it.title}</a>
              </li>
            ))}
            {!loading && items.length === 0 && <li className="text-gray-400 text-sm">No headlines available.</li>}
          </ul>
        </div>
        <div>
          <div className="text-xs text-gray-400 mb-2">Earnings announcements</div>
          <ul className="space-y-2">
            {(earnings||[]).slice(0,8).map((e, i) => (
              <li key={i} className="text-sm">
                <a href={e.link} target="_blank" rel="noopener noreferrer" className="text-white/90 hover:text-white underline-offset-2 hover:underline">{e.ticker}</a>
                <span className="text-gray-400 text-xs"> — filing {e.filing_date || 'N/A'} (period {e.period || 'N/A'})</span>
              </li>
            ))}
            {(earnings||[]).length===0 && <li className="text-gray-400 text-sm">No earnings data yet.</li>}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NewsSection;