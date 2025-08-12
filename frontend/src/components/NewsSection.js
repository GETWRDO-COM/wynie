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

  const top = items.slice(0,6);
  const more = items.slice(6,20);
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
          <ul className="divide-y divide-white/10">
            {loading && <li className="text-gray-400 text-sm py-2">Loading headlines…</li>}
            {!loading && top.map((it, idx) => (
              <li key={idx} className="py-2 flex items-center gap-3">
                {it.thumb && <img src={it.thumb} alt="thumb" className="w-16 h-12 object-cover rounded border border-white/10" />}
                <div className="min-w-0">
                  <a href={it.link} target="_blank" rel="noopener noreferrer" className="text-white/90 hover:text-white underline-offset-2 hover:underline line-clamp-2">{it.title}</a>
                  <div className="text-[11px] text-gray-400 mt-1">
                    {it.source && <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 mr-2">{it.source}</span>}
                    {it.published && <span>{new Date(it.published).toLocaleString()}</span>}
                  </div>
                </div>
              </li>
            ))}
            {!loading && top.length === 0 && <li className="text-gray-400 text-sm py-2">No headlines available.</li>}
          </ul>
          {more.length>0 && (
            <div className="mt-3">
              <details>
                <summary className="cursor-pointer text-xs text-blue-400 hover:text-blue-300">See more</summary>
                <ul className="divide-y divide-white/10 mt-2">
                  {more.map((it, idx) => (
                    <li key={idx} className="py-2 flex items-center gap-3">
                      {it.thumb && <img src={it.thumb} alt="thumb" className="w-12 h-10 object-cover rounded border border-white/10" />}
                      <div className="min-w-0">
                        <a href={it.link} target="_blank" rel="noopener noreferrer" className="text-white/90 hover:text-white underline-offset-2 hover:underline line-clamp-2">{it.title}</a>
                        <div className="text-[11px] text-gray-400 mt-1">
                          {it.source && <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 mr-2">{it.source}</span>}
                          {it.published && <span>{new Date(it.published).toLocaleString()}</span>}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </details>
            </div>
          )}
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