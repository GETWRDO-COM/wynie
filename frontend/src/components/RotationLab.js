import React, { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';

// Info icon with tooltip
function Info({text}){
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex items-center">
      <button type="button" onMouseEnter={()=>setOpen(true)} onMouseLeave={()=>setOpen(false)} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} className="inline-flex items-center justify-center w-4 h-4 rounded-full border border-white/30 text-[10px] text-white/90 bg-white/10 hover:bg-white/20 shadow-[0_0_12px_rgba(0,255,255,0.25)] ml-1 align-middle">i</button>
      {open && (
        <div className="absolute z-50 top-5 left-1/2 -translate-x-1/2 min-w-[240px] max-w-[360px] text-xs text-white bg-black/90 border border-white/15 rounded-lg p-2 shadow-xl">
          {text}
        </div>
      )}
    </span>
  );
}

function NumberInput({label, value, onChange, step=1, min=0, hint}){
  return (
    <label className="block">
      <div className="text-xs text-gray-300 mb-1 flex items-center gap-1">{label}{hint && <Info text={hint} />}</div>
      <input type="number" value={Number.isFinite(value)?value:''} onChange={e=>onChange(parseFloat(e.target.value))} step={step} min={min} className="form-input w-full" />
    </label>
  );
}

function TextInput({label, value, onChange, hint}){
  return (
    <label className="block">
      <div className="text-xs text-gray-300 mb-1 flex items-center gap-1">{label}{hint && <Info text={hint} />}</div>
      <input value={value||''} onChange={e=>onChange(e.target.value)} className="form-input w-full" />
    </label>
  );
}

function toCSV(rows, headers){
  const esc = (v)=>`"${String(v??'').replaceAll('"','""')}"`;
  const head = headers.map(esc).join(',');
  const body = rows.map(r=>headers.map(h=>esc(r[h])).join(',')).join('\n');
  return head+'\n'+body;
}

function download(name, text){
  const blob = new Blob([text], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = name; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url);
}

const BUILTIN_PRESETS = {
  'Keltner + EMA + 200 DMA': {
    ema_fast: 20, ema_slow: 50, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 2, conf_threshold: 2, exec_timing: 'next_open',
    cost_bps: 5, slippage_bps: 5
  },
  'DMA 50/200 (no Keltner)': {
    ema_fast: 50, ema_slow: 200, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 2, conf_threshold: 2, exec_timing: 'next_open',
    cost_bps: 5, slippage_bps: 5
  },
  'Conservative (More Confirmation)': {
    ema_fast: 20, ema_slow: 50, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 3, conf_threshold: 3, exec_timing: 'next_open',
    cost_bps: 5, slippage_bps: 5
  },
  'Aggressive (Faster Entries)': {
    ema_fast: 20, ema_slow: 50, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 1, conf_threshold: 2, exec_timing: 'close',
    cost_bps: 5, slippage_bps: 5
  }
};

const SeasonMonths = ({value, onChange})=>{
  const months = ['1','2','3','4','5','6','7','8','9','10','11','12'];
  const selected = new Set(String(value||'').split(',').map(s=>s.trim()).filter(Boolean));
  const toggle = (m)=>{ const set=new Set(selected); if(set.has(m)) set.delete(m); else set.add(m); onChange(Array.from(set).sort((a,b)=>Number(a)-Number(b)).join(',')); };
  return (
    <div className="flex flex-wrap gap-1">
      {months.map(m=> (
        <button key={m} type="button" onClick={()=>toggle(m)} className={`px-2 py-0.5 rounded text-xs border ${selected.has(m)?'bg-white/15 text-white border-white/20':'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10'}`}>{m}</button>
      ))}
    </div>
  );
};

const RotationLab = ({ api }) => {
  const RAW_BASE = process.env.REACT_APP_BACKEND_URL || '';
  const BASE = RAW_BASE.replace(/\/$/, '');
  const buildUrl = (path) => {
    // Normalize to avoid double /api when BASE already ends with /api
    if (!BASE) return path; // fallback to relative '/api/...'
    const p = path.startsWith('/api') && BASE.endsWith('/api') ? path.replace(/^\/api/, '') : path;
    return `${BASE}${p}`;
  };
  const authHeaders = () => { const t = localStorage.getItem('authToken'); return t ? { Authorization: `Bearer ${t}` } : {}; };
  const httpGet = async (path) => { const url = buildUrl(path); const res = await fetch(url, { headers: { 'Content-Type':'application/json', ...authHeaders() } }); if(!res.ok) throw new Error(`GET ${path} ${res.status}`); return res.json(); };
  const httpPost = async (path, body) => { const url = buildUrl(path); const res = await fetch(url, { method:'POST', headers: { 'Content-Type':'application/json', ...authHeaders() }, body: JSON.stringify(body) }); if(!res.ok) throw new Error(`POST ${path} ${res.status}`); return res.json(); };
  const httpDelete = async (path) => { const url = buildUrl(path); const res = await fetch(url, { method:'DELETE', headers: { ...authHeaders() } }); if(!res.ok) throw new Error(`DELETE ${path} ${res.status}`); return res.json(); };
  const [cfg, setCfg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [live, setLive] = useState(null);
  const [bt, setBt] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [presetKey, setPresetKey] = useState('Keltner + EMA + 200 DMA');
  const [userPresets, setUserPresets] = useState([]);
  const [howOpen, setHowOpen] = useState(true);

  // A/B compare
  const [compA, setCompA] = useState(null);
  const [compB, setCompB] = useState(null);
  const [resA, setResA] = useState(null);
  const [resB, setResB] = useState(null);
  const [comparing, setComparing] = useState(false);

  const [diag, setDiag] = useState({ base:'', url:'', token:false, last:'' });
  useEffect(()=>{ (async()=>{ try{ const token = !!localStorage.getItem('authToken'); const url = (RAW_BASE||'') + '/api/rotation/config'; setDiag(d=>({ ...d, base: RAW_BASE||'', url, token })); const data = await httpGet('/api/rotation/config'); setCfg(data.config || data); } catch(err){ setDiag(d=>({ ...d, last: String(err?.message||err) })); // attempt to upsert default config then re-get
      try { const def = { name:'Default', capital:100000, rebalance:'D', trend_days:200, ema_fast:20, ema_slow:50, rsi_len:14, atr_len:20, kelt_mult:2.0, macd_fast:12, macd_slow:26, macd_signal:9, consec_needed:2, conf_threshold:2, exec_timing:'next_open', pairs:[{bull:'TQQQ', bear:'SQQQ', underlying:'QQQ'}] };
        await httpPost('/api/rotation/config', def); const data2 = await httpGet('/api/rotation/config'); setCfg(data2.config || data2); } catch(e2){ setDiag(d=>({ ...d, last: `Fallback failed: ${String(e2?.message||e2)}` })); }
    } finally { setLoading(false); } })(); }, []);
  const loadPresets = async()=>{ try{ const r = await httpGet('/api/rotation/presets'); setUserPresets(r.items||[]); } catch{} };
  useEffect(()=>{ loadPresets(); }, []);

  const applyPreset = (key)=>{
    if(!cfg) return;
    const built = BUILTIN_PRESETS[key];
    const usr = (userPresets.find(p=>p.name===key)?.config) || null;
    const p = usr || built; if(!p) return;
    const pairs = (cfg.pairs && cfg.pairs.length) ? cfg.pairs : [{bull:'TQQQ', bear:'SQQQ', underlying:'QQQ'}];
    setCfg({...cfg, ...p, pairs});
    setPresetKey(key);
  };

  const savePreset = async()=>{
    const name = prompt('Preset name');
    if(!name) return;
    try{
      await httpPost('/api/rotation/presets', { name, config: cfg });
      await loadPresets();
      setPresetKey(name);
    } catch { alert('Failed to save preset'); }
  };
  const deletePreset = async(name)=>{ if(!confirm(`Delete preset "${name}"?`)) return; try{ await httpDelete(`/api/rotation/presets/${encodeURIComponent(name)}`); await loadPresets(); } catch { alert('Failed to delete'); } };

  const save = async()=>{ setSaving(true); try{ await api.post('/api/rotation/config', cfg); } finally { setSaving(false);} };
  const reloadLive = async()=>{ const r = await api.get('/api/rotation/live'); setLive(r.data); };
  const runBacktest = async()=>{ setRunning(true); try{ const r = await api.post('/api/rotation/backtest', cfg); setBt(r.data); setResA(null); setResB(null);} finally { setRunning(false);} };

  const uploadXLSX = async (file) => {
    setUploading(true);
    try{
      const fd = new FormData();
      fd.append('file', file);
      const r = await api.post('/api/rotation/upload-xlsx', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      alert(`Parsed sheets: ${r.data.sheets.join(', ')}`);
    } catch(e){ alert('Upload failed'); } finally { setUploading(false); }
  };

  const compareVsPreset = async()=>{
    const p = BUILTIN_PRESETS[presetKey] || (userPresets.find(x=>x.name===presetKey)?.config);
    if(!p){ alert('Select a preset to compare against'); return; }
    setCompA({...cfg, ...p});
    setCompB({...cfg});
    setComparing(true);
    try{
      const [ra, rb] = await Promise.all([
        api.post('/api/rotation/backtest', {...cfg, ...p}),
        api.post('/api/rotation/backtest', cfg),
      ]);
      setResA(ra.data); setResB(rb.data);
    } finally { setComparing(false); }
  };

  // Charts from primary backtest
  const equityData = useMemo(()=>{
    if(!bt?.equity_curve?.length) return null;
    const labels = bt.equity_curve.map(p=>p.date);
    const values = bt.equity_curve.map(p=>p.equity);
    return { labels, datasets: [{ label: 'Equity', data: values, borderColor: 'rgb(56,189,248)', backgroundColor: 'rgba(56,189,248,0.14)', fill: true, tension: 0.25, pointRadius: 0, borderWidth: 2 }] };
  }, [bt]);
  const ddData = useMemo(()=>{
    if(!bt?.drawdown?.length) return null;
    const labels = bt.drawdown.map(p=>p.date);
    const values = bt.drawdown.map(p=> (p.dd*100).toFixed(2));
    return { labels, datasets: [{ label: 'Drawdown %', data: values, borderColor: 'rgb(248,113,113)', backgroundColor: 'rgba(248,113,113,0.16)', fill: true, tension: 0.25, pointRadius: 0, borderWidth: 2 }] };
  }, [bt]);

  // A/B overlay charts
  const overlayEq = useMemo(()=>{
    if(!resA?.equity_curve || !resB?.equity_curve) return null;
    const labels = resA.equity_curve.map(p=>p.date);
    return { labels, datasets: [
      { label: 'A Equity', data: resA.equity_curve.map(p=>p.equity), borderColor: 'rgb(99,102,241)', backgroundColor:'rgba(99,102,241,0.15)', fill:true, tension:0.25, pointRadius:0 },
      { label: 'B Equity', data: resB.equity_curve.map(p=>p.equity), borderColor: 'rgb(34,197,94)', backgroundColor:'rgba(34,197,94,0.15)', fill:true, tension:0.25, pointRadius:0 },
    ]};
  }, [resA,resB]);
  const overlayDD = useMemo(()=>{
    if(!resA?.drawdown || !resB?.drawdown) return null;
    const labels = resA.drawdown.map(p=>p.date);
    return { labels, datasets: [
      { label: 'A DD %', data: resA.drawdown.map(p=>(p.dd*100).toFixed(2)), borderColor:'rgb(244,114,182)', backgroundColor:'rgba(244,114,182,0.15)', fill:true, tension:0.25, pointRadius:0 },
      { label: 'B DD %', data: resB.drawdown.map(p=>(p.dd*100).toFixed(2)), borderColor:'rgb(251,191,36)', backgroundColor:'rgba(251,191,36,0.15)', fill:true, tension:0.25, pointRadius:0 },
    ]};
  }, [resA,resB]);

  // Monthly heatmap (from primary backtest)
  const monthly = useMemo(()=>{
    if(!bt?.equity_curve?.length) return null;
    const parse = (s)=> new Date(s);
    const byMonth = new Map();
    bt.equity_curve.forEach(p=>{ const d=parse(p.date); const key=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; byMonth.set(key, p.equity); });
    const keys = Array.from(byMonth.keys()).sort();
    const rowsMap = new Map(); let prev = null;
    keys.forEach(k=>{ const [y,m] = k.split('-'); const eq = byMonth.get(k); if(prev!=null){ const ret = (eq/prev-1); const row = rowsMap.get(y) || {}; row[m]=ret; rowsMap.set(y,row); } prev = eq; });
    const years = Array.from(rowsMap.keys()).sort();
    const months = ['01','02','03','04','05','06','07','08','09','10','11','12'];
    return { years, months, rows: rowsMap };
  }, [bt]);
  const heatColor = (v)=>{
    if(v==null) return 'bg-white/5';
    const x = Math.max(-0.2, Math.min(0.2, v));
    if(x>=0){ return `bg-[rgba(34,197,94,${0.25+0.55*(x/0.2)})] text-white`; }
    return `bg-[rgba(239,68,68,${0.25+0.55*(-x/0.2)})] text-white`;
  };

  // KPI
  const kpi = bt?.metrics || null;
  const fmtPct = (x)=> x==null? '--' : (x*100).toFixed(2)+'%';
  const fmt = (x)=> x==null? '--' : Number(x).toFixed(2);

  const initDefault = async()=>{
    try{
      const def = { name:'Default', capital:100000, rebalance:'D', trend_days:200, ema_fast:20, ema_slow:50, rsi_len:14, atr_len:20, kelt_mult:2.0, macd_fast:12, macd_slow:26, macd_signal:9, consec_needed:2, conf_threshold:2, exec_timing:'next_open', pairs:[{bull:'TQQQ', bear:'SQQQ', underlying:'QQQ'}] };
      await httpPost('/api/rotation/config', def);
      const data2 = await httpGet('/api/rotation/config'); setCfg(data2.config || data2);
    } catch(e){ setDiag(d=>({ ...d, last: `Init failed: ${String(e?.message||e)}` })); }
  };
  const retryLoad = async()=>{ try{ const data = await httpGet('/api/rotation/config'); setCfg(data.config || data); } catch(e){ setDiag(d=>({ ...d, last: `Retry failed: ${String(e?.message||e)}` })); }};
  const reauth = ()=>{ localStorage.removeItem('authToken'); localStorage.removeItem('user'); window.location.reload(); };

  if (loading) return <div className="glass-panel p-4">Loading Rotation Lab…</div>;
  if (!cfg) return (
    <div className="space-y-3">
      <div className="glass-panel p-3 text-[11px] text-gray-300">
        <div>Backend base: <span className="text-white/90">{diag.base||'(empty)'}</span></div>
        <div>Config URL: <span className="text-white/90">{diag.url}</span></div>
        <div>Auth token present: <span className="text-white/90">{String(diag.token)}</span></div>
        {diag.last && <div>Last error: <span className="text-rose-300">{diag.last}</span></div>}
      </div>
      <div className="glass-panel p-4">
        <div className="text-white/90 font-semibold mb-2">Rotation Lab</div>
        <div className="text-xs text-gray-400 mb-3">We couldn’t load your configuration. Use one of the recovery actions below.</div>
        <div className="flex items-center gap-2 justify-end">
          <button onClick={reauth} className="btn btn-outline text-xs py-1">Re‑authenticate</button>
          <button onClick={retryLoad} className="btn btn-outline text-xs py-1">Retry</button>
          <button onClick={initDefault} className="btn btn-primary-strong text-xs py-1">Initialize Default Config</button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6" key="rotation-v3-20250612">
      {/* Hero header */}
      <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-[#0b0f1a]/80 to-[#0c1222]/80 backdrop-blur-xl p-6">
        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-3">
          <div>
            <div className="text-xs text-cyan-300/80 mb-1">Strategy Workspace</div>
            <div className="text-white font-extrabold text-3xl">Rotation Lab</div>
            <div className="text-sm text-gray-300 mt-1">Build, backtest, and compare leveraged pair rotation strategies.</div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="text-xs text-gray-300">Preset</div>
            <div className="flex items-center gap-2">
              <select value={presetKey} onChange={(e)=>{ setPresetKey(e.target.value); applyPreset(e.target.value); }} className="form-input text-sm min-w-[240px]">
                {Object.keys(BUILTIN_PRESETS).map(k=> <option key={k} value={k}>{k}</option>)}
                {userPresets.length>0 && <optgroup label="Your Presets">{userPresets.map(p=> <option key={p.name} value={p.name}>{p.name}</option>)}</optgroup>}
              </select>
              {userPresets.length>0 && (
                <button onClick={()=>deletePreset(presetKey)} className="btn btn-outline text-xs py-1" title="Delete selected preset">Delete</button>
              )}
              <button onClick={savePreset} className="btn btn-outline text-xs py-1" title="Save current settings as preset">Save as Preset</button>
              <button onClick={compareVsPreset} disabled={comparing} className="btn btn-outline text-xs py-1" title="Compare current vs selected preset">{comparing? 'Comparing…':'Compare vs Preset'}</button>
            </div>
          </div>
        </div>
        {/* How it works banner */}
        <div className="mt-4 rounded-xl border border-white/10 bg-black/30 p-3">
          <div className="flex items-center justify-between">
            <div className="text-white/90 font-semibold">How it works</div>
            <button className="text-xs text-gray-300 underline" onClick={()=>setHowOpen(!howOpen)}>{howOpen? 'Hide':'Show'}</button>
          </div>
          {howOpen && (
            <ol className="mt-2 grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-gray-300 list-decimal list-inside">
              <li>Choose a preset (or adjust settings)</li>
              <li>Add pair(s): e.g., TQQQ/SQQQ on QQQ</li>
              <li>Click Backtest</li>
              <li>Review KPIs, charts, heatmap, trades</li>
              <li>Export CSVs or Compare vs Preset</li>
            </ol>
          )}
        </div>
      </div>

      {/* Configuration (Simple + Advanced) */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-white/90 font-semibold">Configuration</div>
            <div className="text-xs text-gray-400">Use these settings to define your strategy.</div>
          </div>
          <button onClick={()=>setShowAdvanced(v=>!v)} className="btn btn-outline text-xs py-1">{showAdvanced? 'Hide Advanced':'Show Advanced'}</button>
        </div>

        {/* Simple controls */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="block">
            <div className="text-xs text-gray-300 mb-1 flex items-center gap-1">Execution Timing<Info text="Select whether trades execute same-day close (uses close) or next-day open (default)." /></div>
            <select value={cfg.exec_timing} onChange={e=>setCfg({...cfg, exec_timing:e.target.value})} className="form-input w-full">
              <option value="next_open">Next-day open</option>
              <option value="close">Same-day close</option>
            </select>
          </label>
          <NumberInput label="Costs (bps)" value={cfg.cost_bps} onChange={v=>setCfg({...cfg, cost_bps:v})} hint="Commission and fees per trade, in basis points." />
          <NumberInput label="Slippage (bps)" value={cfg.slippage_bps} onChange={v=>setCfg({...cfg, slippage_bps:v})} hint="Assumed slippage per trade, in basis points." />
        </div>

        {/* Seasonality */}
        <div className="mt-4">
          <div className="text-xs text-gray-300 mb-1 flex items-center gap-2">Seasonality (In-Season months)<Info text="Restrict trading to selected calendar months. Off = trade all year." /></div>
          <div className="flex items-center gap-3">
            <label className="inline-flex items-center gap-2 text-xs text-gray-300">
              <input type="checkbox" checked={!!cfg.use_inseason} onChange={e=>setCfg({...cfg, use_inseason:e.target.checked})} /> Enable
            </label>
            <SeasonMonths value={cfg.season_months} onChange={v=>setCfg({...cfg, season_months:v})} />
          </div>
        </div>

        {/* Advanced controls */}
        {showAdvanced && (
          <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
            <NumberInput label="Trend Days (200)" value={cfg.trend_days} onChange={v=>setCfg({...cfg, trend_days:v})} hint="200-day SMA regime filter (price above = bull regime, below = bear)." />
            <NumberInput label="EMA Fast (20)" value={cfg.ema_fast} onChange={v=>setCfg({...cfg, ema_fast:v})} hint="Short EMA length used in DualUp (EMAfast > EMAslow)." />
            <NumberInput label="EMA Slow (50)" value={cfg.ema_slow} onChange={v=>setCfg({...cfg, ema_slow:v})} hint="Long EMA length used in DualUp (EMAfast > EMAslow)." />
            <NumberInput label="RSI Length (14)" value={cfg.rsi_len} onChange={v=>setCfg({...cfg, rsi_len:v})} hint="RSI period; >50 contributes to bull confirmations; <50 contributes to bear." />
            <NumberInput label="ATR Length (20)" value={cfg.atr_len} onChange={v=>setCfg({...cfg, atr_len:v})} hint="ATR length used for Keltner bands (EMA20 ± mult × ATR)." />
            <NumberInput label="Keltner Multiplier (2.0)" value={cfg.kelt_mult} onChange={v=>setCfg({...cfg, kelt_mult:v})} step={0.1} hint="Multiplier for ATR to set Keltner upper/lower bands (2.0 typical)." />
            <NumberInput label="MACD Fast" value={cfg.macd_fast} onChange={v=>setCfg({...cfg, macd_fast:v})} hint="Standard MACD parameters; bullish when MACD line > signal." />
            <NumberInput label="MACD Slow" value={cfg.macd_slow} onChange={v=>setCfg({...cfg, macd_slow:v})} />
            <NumberInput label="MACD Signal" value={cfg.macd_signal} onChange={v=>setCfg({...cfg, macd_signal:v})} />
            <NumberInput label="Consecutive DualUp Days" value={cfg.consec_needed} onChange={v=>setCfg({...cfg, consec_needed:v})} hint="Minimum consecutive days with EMAfast>EMAslow required before a long entry (reduces whipsaws)." />
            <NumberInput label="Confirmation Threshold" value={cfg.conf_threshold} onChange={v=>setCfg({...cfg, conf_threshold:v})} hint="How many bullish confirmations required (DualUp, Trend>200DMA, Kelt>upper, MACD bull, RSI>50)." />
          </div>
        )}

        {/* Bottom-right actions */}
        <div className="mt-5 flex items-center justify-end gap-2">
          <button onClick={save} disabled={saving} className="btn btn-outline text-xs py-1">{saving?'Saving…':'Save'}</button>
          <button onClick={reloadLive} className="btn btn-outline text-xs py-1">Recompute Live</button>
          <button onClick={runBacktest} disabled={running} className="btn btn-primary-strong text-xs py-1">{running?'Running…':'Backtest'}</button>
        </div>
      </div>

      {/* Universe & Pairs */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-3">
          <div>
            <div className="text-white/90 font-semibold">Universe & Pairs</div>
            <div className="text-xs text-gray-400">Specify the leveraged pair to trade, and the underlying used for signals (e.g., TQQQ/SQQQ on QQQ).</div>
          </div>
          <div className="flex items-center gap-2">
            <label className="btn btn-outline text-xs py-1 cursor-pointer">
              Upload XLSX
              <input type="file" className="hidden" accept=".xlsx,.xls" onChange={(e)=>{ if(e.target.files?.[0]) uploadXLSX(e.target.files[0]); }} />
            </label>
            <button onClick={()=>setCfg({...cfg, pairs:[...cfg.pairs, {bull:'TQQQ', bear:'SQQQ', underlying:'QQQ'}]})} className="btn btn-outline text-xs py-1">Add Pair</button>
          </div>
        </div>
        <div className="space-y-2">
          {(cfg.pairs||[]).map((p, idx)=>(
            <div key={idx} className="grid grid-cols-1 md:grid-cols-6 gap-3 items-center">
              <TextInput label="Bull" value={p.bull} onChange={v=>{ const arr=[...cfg.pairs]; arr[idx]={...arr[idx], bull:v}; setCfg({...cfg, pairs:arr}); }} />
              <TextInput label="Bear" value={p.bear} onChange={v=>{ const arr=[...cfg.pairs]; arr[idx]={...arr[idx], bear:v}; setCfg({...cfg, pairs:arr}); }} />
              <TextInput label="Underlying" value={p.underlying || 'QQQ'} onChange={v=>{ const arr=[...cfg.pairs]; arr[idx]={...arr[idx], underlying:v}; setCfg({...cfg, pairs:arr}); }} />
              <div className="md:col-span-2" />
              <button onClick={()=>{ const arr=[...cfg.pairs]; arr.splice(idx,1); setCfg({...cfg, pairs:arr}); }} className="btn btn-outline text-xs py-1">Remove</button>
            </div>
          ))}
          {(cfg.pairs||[]).length===0 && <div className="text-xs text-gray-400">No pairs. Add one to begin.</div>}
        </div>
      </div>

      {/* KPI Summary */}
      {kpi && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="rounded-xl bg-black/30 border border-white/10 p-4">
            <div className="text-[11px] text-gray-400 flex items-center gap-1">CAGR<Info text="Compound Annual Growth Rate of the equity curve." /></div>
            <div className="text-2xl font-extrabold text-emerald-300">{fmtPct(kpi.cagr)}</div>
          </div>
          <div className="rounded-xl bg-black/30 border border-white/10 p-4">
            <div className="text-[11px] text-gray-400 flex items-center gap-1">Max Drawdown<Info text="Worst peak-to-trough loss." /></div>
            <div className="text-2xl font-extrabold text-rose-300">{fmtPct(kpi.max_dd)}</div>
          </div>
          <div className="rounded-xl bg-black/30 border border-white/10 p-4">
            <div className="text-[11px] text-gray-400 flex items-center gap-1">Sharpe<Info text="Risk-adjusted return (assumes daily returns, 0% rf)." /></div>
            <div className="text-2xl font-extrabold text-cyan-300">{fmt(kpi.sharpe)}</div>
          </div>
          <div className="rounded-xl bg-black/30 border border-white/10 p-4">
            <div className="text-[11px] text-gray-400 flex items-center gap-1">Total Return<Info text="Overall return from start to end." /></div>
            <div className="text-2xl font-extrabold text-indigo-300">{fmtPct(kpi.total_return)}</div>
          </div>
        </div>
      )}

      {/* Charts */}
      {bt && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
          <div className="glass-panel p-6 xl:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-white/90 font-semibold">Equity Curve</div>
                <div className="text-xs text-gray-400">Portfolio value over time.</div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={()=>{
                  if(!bt) return; const rows = (bt.equity_curve||[]).map((p,idx)=>({date:p.date, equity:p.equity, drawdown: bt.drawdown?.[idx]?.dd ?? ''}));
                  download('rotation_equity.csv', toCSV(rows, ['date','equity','drawdown']));
                }} className="btn btn-outline text-xs py-1">Export CSV</button>
              </div>
            </div>
            {equityData ? (<div className="h-72"><Line data={equityData} options={{responsive:true, plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:true, grid:{color:'rgba(255,255,255,0.05)'}, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Run a backtest to see results.</div>)}
          </div>
          <div className="glass-panel p-6">
            <div className="text-white/90 font-semibold mb-1">Drawdown</div>
            <div className="text-xs text-gray-400 mb-2">Peak-to-trough losses as percentage.</div>
            {ddData ? (<div className="h-72"><Line data={ddData} options={{responsive:true, plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:true, grid:{color:'rgba(255,255,255,0.05)'}, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Run a backtest.</div>)}
          </div>
        </div>
      )}

      {/* Monthly Heatmap */}
      {bt && monthly && (
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-white/90 font-semibold">Monthly Returns Heatmap</div>
              <div className="text-xs text-gray-400">End-of-month returns based on equity curve. Darker = larger magnitude.</div>
            </div>
            <button onClick={()=>{
              if(!bt) return; const rows = (bt.equity_curve||[]).map((p,idx)=>({date:p.date, equity:p.equity, drawdown: bt.drawdown?.[idx]?.dd ?? ''}));
              download('rotation_equity.csv', toCSV(rows, ['date','equity','drawdown']));
            }} className="btn btn-outline text-xs py-1">Export Equity CSV</button>
          </div>
          <div className="overflow-auto max-h-96">
            <table className="min-w-[720px] text-xs">
              <thead className="sticky top-0 bg-black/70 backdrop-blur z-10">
                <tr>
                  <th className="px-2 py-1 text-left text-gray-400 sticky left-0 bg-black/70">Year</th>
                  {monthly.months.map(m=> (<th key={m} className="px-2 py-1 text-gray-400">{m}</th>))}
                </tr>
              </thead>
              <tbody>
                {monthly.years.map(y=>{
                  const row = monthly.rows.get(y) || {};
                  return (
                    <tr key={y}>
                      <td className="px-2 py-1 text-gray-400 sticky left-0 bg-black/40 backdrop-blur z-10">{y}</td>
                      {monthly.months.map(m=>{
                        const v = row[m];
                        const pct = v!=null? (v*100).toFixed(1)+'%': '';
                        return <td key={m} className={`px-2 py-1 text-center rounded ${heatColor(v)}`}>{pct}</td>;
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Trades */}
      {bt && (
        <div className="glass-panel p-6">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="text-white/90 font-semibold">Trades</div>
              <div className="text-xs text-gray-400">Executed buys and sells with size and price.</div>
            </div>
            <button onClick={()=>{
              if(!bt) return; const rows = (bt.trades||[]).map(t=>({date:t.date, action:t.action, ticker:t.ticker, shares:t.shares, price:t.price}));
              download('rotation_trades.csv', toCSV(rows, ['date','action','ticker','shares','price']));
            }} className="btn btn-outline text-xs py-1">Export CSV</button>
          </div>
          <div className="overflow-auto max-h-96">
            <table className="min-w-[640px] text-xs">
              <thead className="sticky top-0 bg-black/70 backdrop-blur z-10">
                <tr className="text-gray-400">
                  <th className="px-2 py-1 text-left">Date</th>
                  <th className="px-2 py-1 text-left">Action</th>
                  <th className="px-2 py-1 text-left">Ticker</th>
                  <th className="px-2 py-1 text-right">Shares</th>
                  <th className="px-2 py-1 text-right">Price</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {(bt.trades||[]).map((t,i)=>(
                  <tr key={i} className="hover:bg-white/5">
                    <td className="px-2 py-1">{t.date}</td>
                    <td className="px-2 py-1">{t.action}</td>
                    <td className="px-2 py-1">{t.ticker}</td>
                    <td className="px-2 py-1 text-right">{Number(t.shares).toFixed(2)}</td>
                    <td className="px-2 py-1 text-right">{Number(t.price).toFixed(2)}</td>
                  </tr>
                ))}
                {(bt.trades||[]).length===0 && <tr><td className="px-2 py-2 text-gray-400" colSpan="5">No trades.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* A/B Compare */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-white/90 font-semibold">A/B Compare</div>
            <div className="text-xs text-gray-400">Compare current configuration against a preset or another saved configuration.</div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={()=>setCompA({...cfg, _label:'A'})} className="btn btn-outline text-xs py-1">Set A from Current</button>
            <button onClick={()=>setCompB({...cfg, _label:'B'})} className="btn btn-outline text-xs py-1">Set B from Current</button>
            <button onClick={compareVsPreset} disabled={comparing} className="btn btn-outline text-xs py-1">{comparing? 'Comparing…':'Compare vs Preset'}</button>
          </div>
        </div>
        {(resA || resB) ? (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
            <div className="rounded-2xl border border-white/10 bg-black/30 p-3 xl:col-span-3">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">A CAGR</div>
                  <div className="text-xl font-extrabold text-indigo-300">{resA? (resA.metrics? (resA.metrics.cagr*100).toFixed(2)+'%':'--') : '--'}</div>
                </div>
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">A Max DD</div>
                  <div className="text-xl font-extrabold text-rose-300">{resA? (resA.metrics? (resA.metrics.max_dd*100).toFixed(2)+'%':'--') : '--'}</div>
                </div>
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">A Sharpe</div>
                  <div className="text-xl font-extrabold text-cyan-300">{resA? (resA.metrics? (resA.metrics.sharpe).toFixed(2):'--') : '--'}</div>
                </div>
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">A Total Return</div>
                  <div className="text-xl font-extrabold text-emerald-300">{resA? (resA.metrics? (resA.metrics.total_return*100).toFixed(2)+'%':'--') : '--'}</div>
                </div>
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">B CAGR</div>
                  <div className="text-xl font-extrabold text-indigo-300">{resB? (resB.metrics? (resB.metrics.cagr*100).toFixed(2)+'%':'--') : '--'}</div>
                </div>
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">B Max DD</div>
                  <div className="text-xl font-extrabold text-rose-300">{resB? (resB.metrics? (resB.metrics.max_dd*100).toFixed(2)+'%':'--') : '--'}</div>
                </div>
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">B Sharpe</div>
                  <div className="text-xl font-extrabold text-cyan-300">{resB? (resB.metrics? (resB.metrics.sharpe).toFixed(2):'--') : '--'}</div>
                </div>
                <div className="rounded-xl bg-black/30 border border-white/10 p-3">
                  <div className="text-[11px] text-gray-400">B Total Return</div>
                  <div className="text-xl font-extrabold text-emerald-300">{resB? (resB.metrics? (resB.metrics.total_return*100).toFixed(2)+'%':'--') : '--'}</div>
                </div>
              </div>
            </div>
            <div className="glass-panel p-6 xl:col-span-2">
              <div className="text-white/90 font-semibold mb-2">Equity Overlay</div>
              {overlayEq ? (<div className="h-72"><Line data={overlayEq} options={{responsive:true, plugins:{legend:{display:true, labels:{color:'#cbd5e1'}}}, scales:{x:{display:false}, y:{display:true, grid:{color:'rgba(255,255,255,0.05)'}, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Set configurations and run compare.</div>)}
            </div>
            <div className="glass-panel p-6">
              <div className="text-white/90 font-semibold mb-2">Drawdown Overlay</div>
              {overlayDD ? (<div className="h-72"><Line data={overlayDD} options={{responsive:true, plugins:{legend:{display:true, labels:{color:'#cbd5e1'}}}, scales:{x:{display:false}, y:{display:true, grid:{color:'rgba(255,255,255,0.05)'}, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Set configurations and run compare.</div>)}
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400">Set A/B and click Compare vs Preset to see overlay charts and KPIs.</div>
        )}
      </div>
    </div>
  );
};

export default RotationLab;