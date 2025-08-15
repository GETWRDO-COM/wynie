import React, { useEffect, useMemo, useState } from 'react';

const FEEDS = { All:'All', USA:'USA', World:'World', 'South Africa':'South Africa', 'Stock Market':'Stock Market', 'Finance News':'Finance News' };

// Heuristic summarizer for ticker headlines
function toNameFromDomain(domain){ try { if(!domain) return ''; const parts = domain.replace(/^www\./,'').split('.'); const core = parts.length>1? parts[parts.length-2]: parts[0]; return core.toUpperCase(); } catch { return ''; } }
const STOP = new Set(['the','a','an','of','to','and','for','with','on','in','at','from','that','this','is','are','was','were','as','by','after','over','into','about']);
function pickWords(str, max=4){ const w = (str||'').split(/\s+/).filter(Boolean).filter(x=>!STOP.has(x.toLowerCase())); return w.slice(0,max).join(' '); }
function summarizeHeadline(title, source){ if(!title) return ''; const t = title.replace(/\s+/g,' ').trim(); const lower = t.toLowerCase(); const catMap = [ ['tsunami','Tsunami'], ['earthquake','Earthquake'], ['quake','Earthquake'], ['hurricane','Hurricane'], ['cyclone','Cyclone'], ['wildfire','Wildfire'], ['fire','Fire'], ['flood','Flood'], ['crash','Plane Crash'], ['plane','Plane'], ['shooting','Shooting'], ['verdict','Verdict'], ['trial','Trial'], ['arrest','Arrest'], ['strike','Strike'], ['earnings','Earnings'], ['layoffs','Layoffs'], ['inflation','Inflation'], ['rates','Rates'], ['stocks','Stocks'], ['market','Market'], ['trump','Trump'] ];
  let cat = null; for(const [k,v] of catMap){ if(lower.includes(k)){ cat = v; break; } }
  let loc = null; const m = t.match(/\bin\s+([A-Z][\w\-]*(?:\s+[A-Z][\w\-]*){0,2})/); if(m) loc = m[1];
  if(!loc){ const parts = t.split(/\s[-–—:]\s/); if(parts.length>1){ const tail = parts[parts.length-1]; loc = pickWords(tail,3); } }
  if(!cat){ const parts = t.split(/[:\-–—]/); cat = pickWords(parts[0]||t,4); }
  if(!loc) loc = toNameFromDomain(source);
  const left = (cat||'').trim(); const right = (loc||'').trim();
  return right ? `${left} — ${right}` : left; }

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

  const parts = useMemo(() => { const arr = loading ? ['Loading news…'] : (items && items.length) ? items.map((it) => summarizeHeadline(it?.title || '', it?.source)) : [error || 'No headlines available']; return arr.filter(Boolean).length ? [...arr] : ['Loading news…']; }, [items, loading, error]);

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
          <div className="relative flex-1 overflow-hidden h-8" aria-live="polite" aria-busy={loading}>
            <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-black/80 via-transparent to-black/80" />
            <div className={`absolute whitespace-nowrap will-change-transform text-base text-white ${parts.length? 'animate-[ticker_5000s_linear_infinite]' : ''}`}>
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
      <style>{`@keyframes ticker { 0% { transform: translateX(0);} 100% { transform: translateX(-100%);} }`}</style>
    </div>
  );
};

export default NewsTicker;