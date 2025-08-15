import React, { useEffect, useMemo, useState } from 'react';

function rel(ts){ if(!ts) return ''; const d=new Date(ts).getTime(); const diff=Math.round((d-Date.now())/60000); const rtf=new Intl.RelativeTimeFormat('en',{numeric:'auto'}); if(Math.abs(diff)<60) return rtf.format(diff,'minute'); const dh=Math.round(diff/60); if(Math.abs(dh)<24) return rtf.format(dh,'hour'); const dd=Math.round(dh/24); return rtf.format(dd,'day'); }

const CATS = ['Watchlist','All','USA','South Africa','Stock Market','Finance News'];

const NewsSection = ({ api }) => {
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
  const [category, setCategory] = useState('All');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [wlTickers, setWlTickers] = useState([]);
  const [earnings, setEarnings] = useState([]);
  const [earningsUpdatedAt, setEarningsUpdatedAt] = useState(null);
  const [showMore, setShowMore] = useState(false);
  const [updatedAt, setUpdatedAt] = useState(null);
  const [compact, setCompact] = useState(true);

  // Cache helpers
  const cacheKey = (cat) => `news:${cat}`;
  const setCached = (cat, arr) => { try { localStorage.setItem(cacheKey(cat), JSON.stringify({ t: Date.now(), items: arr })); } catch {} };
  const getCached = (cat) => { try { const raw = localStorage.getItem(cacheKey(cat)); if (!raw) return null; const js = JSON.parse(raw); return js?.items || null; } catch { return null; } };

  useEffect(() => {
    (async () => {
      try {
        const r = await api.get('/api/watchlists/custom');
        const all = r.data || [];
        const symbols = new Set();
        all.forEach(wl => (wl.stocks||[]).forEach(s => { if (s?.symbol) symbols.add((s.symbol||s.ticker||'').toUpperCase()); }));
        const list = Array.from(symbols).slice(0, 20);
        setWlTickers(list);
        // Load earnings with fallback if empty
        const loadEarnings = async () => {
          try {
            let url;
            if (list.length) {
              url = `${BACKEND_URL}/api/earnings?tickers=${encodeURIComponent(list.join(','))}`;
            } else {
              url = `${BACKEND_URL}/api/earnings?days_ahead=14`;
            }
            const er = await fetch(url);
            const ej = await er.json();
            const items = Array.isArray(ej.items) ? ej.items : [];
            if (items.length === 0 && list.length) {
              const ef = await fetch(`${BACKEND_URL}/api/earnings?days_ahead=14`);
              const jf = await ef.json();
              setEarnings(Array.isArray(jf.items) ? jf.items : []);
              setEarningsUpdatedAt(new Date());
            } else {
              setEarnings(items);
              setEarningsUpdatedAt(new Date());
            }
          } catch { setEarnings([]); setEarningsUpdatedAt(new Date()); }
        };
        await loadEarnings();
      } catch { /* ignore */ }
    })();
  }, []);

  const fetchNews = async (cat) => {
    setLoading(true); setErr('');
    try {
      let url;
      if (cat === 'Watchlist') {
        if (!wlTickers.length) url = `${BACKEND_URL}/api/news?category=${encodeURIComponent('All')}`; else { const q = wlTickers.slice(0,6).join(' OR '); url = `${BACKEND_URL}/api/news?q=${encodeURIComponent(q)}`; }
      } else {
        url = `${BACKEND_URL}/api/news?category=${encodeURIComponent(cat)}`;
      }
      const resp = await fetch(url);
      const data = await resp.json();
      const parsed = (data && data.items) ? data.items : [];
      // Fallback if empty
      if (!parsed.length && cat !== 'All') {
        const r = await fetch(`${BACKEND_URL}/api/news?category=${encodeURIComponent('All')}`);
        const d = await r.json();
        const p2 = d?.items || [];
        setItems(p2);
        setCached('All', p2);
      } else {
        setItems(parsed);
        setCached(cat, parsed);
      }
      setUpdatedAt(new Date());
    } catch (e) {
      const cached = getCached(cat) || getCached('All');
      if (cached) {
        setItems(cached);
      } else {
        setErr('News unavailable'); setItems([]);
      }
      setUpdatedAt(new Date());
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchNews(category); }, [category, wlTickers.join(',')]);

  const top = items.slice(0,6);
  const more = items.slice(6,20);
  const updatedRel = rel(updatedAt);
  const earningsUpdatedRel = rel(earningsUpdatedAt);

  const renderThumb = (it, size='lg') => {
    const thumb = it.thumb || (it.source ? `https://logo.clearbit.com/${it.source}` : null);
    const cls = size==='lg' ? 'w-24 h-16' : 'w-16 h-12';
    return thumb ? <img src={thumb} alt="thumb" className={`${cls} object-cover rounded border border-white/10`} onError={(e)=>{ e.currentTarget.style.display='none'; }} /> : <div className={`${cls} rounded bg-white/5 border border-white/10`} />;
  };

  return (
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-white/90 font-semibold">Top Headlines</div>
        <div className="flex items-center gap-2">
          <button onClick={()=> setCompact(v=>!v)} className="btn btn-outline text-xs py-1">{compact? 'Expanded' : 'Compact'}</button>
          <div className="flex flex-wrap gap-2">
            {CATS.map(c => (
              <button key={c} onClick={() => { setShowMore(false); setCategory(c); }} className={`px-3 py-1.5 rounded-lg text-xs ${category===c?'text-white bg-white/10 border border-white/10':'text-gray-300 hover:text-white hover:bg-white/5'}`}>{c}</button>
            ))}
          </div>
        </div>
      </div>
      <div className="text-[11px] text-gray-500 mb-2">{updatedRel ? `Updated ${updatedRel}` : ''}</div>
      {err && <div className="text-xs text-amber-300 mb-2">{err}</div>}
      <div className={`grid grid-cols-1 ${compact? 'md:grid-cols-2' : 'md:grid-cols-2'} gap-3`}>
        <div>
          <ul className="divide-y divide-white/10">
            {loading && <li className="text-gray-400 text-sm py-2">Loading headlines…</li>}
            {!loading && top.map((it, idx) => (
              <li key={idx} className="py-2 flex items-center gap-3">
                {renderThumb(it,'lg')}
                <div className="min-w-0">
                  <a href={it.link} target="_blank" rel="noopener noreferrer" className="text-white/90 hover:text-white underline-offset-2 hover:underline line-clamp-2">{it.title}</a>
                  <div className="text-[11px] text-gray-400 mt-1 flex items-center gap-2">
                    {it.source && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/5 border border-white/10 mr-1">
                        <img src={`https://logo.clearbit.com/${it.source}`} alt="src" className="w-3 h-3 rounded" onError={(e)=>{e.currentTarget.style.display='none';}} />
                        <span>{it.source}</span>
                      </span>
                    )}
                    {it.published && <span>{rel(it.published)}</span>}
                  </div>
                </div>
              </li>
            ))}
            {!loading && top.length === 0 && <li className="text-gray-400 text-sm py-2">No headlines available.</li>}
          </ul>
          <div className="flex items-center justify-end mt-3">
            <button onClick={()=>{ setShowMore(v=>!v); }} className="btn btn-outline text-xs py-1">{showMore?'Hide':'See more'}</button>
          </div>
          {showMore && (
            <ul className="divide-y divide-white/10 mt-2">
              {more.map((it, idx) => (
                <li key={idx} className="py-2 flex items-center gap-3">
                  {renderThumb(it,'sm')}
                  <div className="min-w-0">
                    <a href={it.link} target="_blank" rel="noopener noreferrer" className="text-white/90 hover:text-white underline-offset-2 hover:underline line-clamp-2">{it.title}</a>
                    <div className="text-[11px] text-gray-400 mt-1 flex items-center gap-2">
                      {it.source && (
                        <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/5 border border-white/10 mr-1">
                          <img src={`https://logo.clearbit.com/${it.source}`} alt="src" className="w-3 h-3 rounded" onError={(e)=>{e.currentTarget.style.display='none';}} />
                          <span>{it.source}</span>
                        </span>
                      )}
                      {it.published && <span>{rel(it.published)}</span>}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs text-white/90 font-semibold flex items-center gap-2"><span className="px-2 py-0.5 rounded bg-gradient-to-r from-green-500/80 to-blue-500/80 text-black">Earnings</span><span className="text-gray-400 font-normal">announcements</span></div>
            <div className="text-[11px] text-gray-500">{earningsUpdatedRel ? `Updated ${earningsUpdatedRel}` : ''}</div>
          </div>
          <ul className="space-y-2 bg-white/5 border border-white/10 rounded-lg p-3">
            {(earnings||[]).slice(0,8).map((e, i) => (
              <li key={i} className="text-sm">
                <a href={e.link} target="_blank" rel="noopener noreferrer" className="text-white/90 hover:text-white underline-offset-2 hover:underline">{e.ticker}</a>
                <span className="text-gray-400 text-xs"> — {e.date || 'N/A'} {e.time? '('+e.time+')':''} {e.period? 'Q'+e.period: ''}</span>
              </li>
            ))}
            {(earnings||[]).length===0 && <li className="text-gray-400 text-sm">No earnings data yet.</li>}
          </ul>
          <div className="flex items-center justify-end mt-3">
            <button onClick={()=>{ setShowMore(false); fetchNews(category); }} className="btn btn-outline text-xs py-1">Reload</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NewsSection;