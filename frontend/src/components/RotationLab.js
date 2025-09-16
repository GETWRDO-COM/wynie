import React, { useEffect, useState } from 'react';

function NumberInput({label, value, onChange, step=1, min=0, hint}){
  return (
    <label className="block">
      <div className="text-xs text-gray-400 mb-1 flex items-center gap-1">{label}{hint && <span className="text-[10px] text-gray-500" title={hint}>ⓘ</span>}</div>
      <input type="number" value={value} onChange={e=>onChange(parseFloat(e.target.value))} step={step} min={min} className="form-input w-full" />
    </label>
  );
}

function TextInput({label, value, onChange, hint}){
  return (
    <label className="block">
      <div className="text-xs text-gray-400 mb-1 flex items-center gap-1">{label}{hint && <span className="text-[10px] text-gray-500" title={hint}>ⓘ</span>}</div>
      <input value={value} onChange={e=>onChange(e.target.value)} className="form-input w-full" />
    </label>
  );
}

const RotationLab = ({ api }) => {
  const [cfg, setCfg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [live, setLive] = useState(null);
  const [bt, setBt] = useState(null);
  const [uploading, setUploading] = useState(false);

  useEffect(()=>{ (async()=>{ try{ const r = await api.get('/api/rotation/config'); setCfg(r.data.config || r.data); } finally { setLoading(false); } })(); }, [api]);

  const save = async()=>{ setSaving(true); try{ await api.post('/api/rotation/config', cfg); } finally { setSaving(false);} };
  const reloadLive = async()=>{ const r = await api.get('/api/rotation/live'); setLive(r.data); };
  const runBacktest = async()=>{ const r = await api.post('/api/rotation/backtest', cfg); setBt(r.data); };

  const uploadXLSX = async (file) => {
    setUploading(true);
    try{
      const fd = new FormData();
      fd.append('file', file);
      const r = await api.post('/api/rotation/upload-xlsx', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      alert(`Parsed sheets: ${r.data.sheets.join(', ')}`);
    } catch(e){
      alert('Upload failed');
    } finally { setUploading(false); }
  };

  if (loading) return <div className="glass-panel p-4">Loading Rotation Lab…</div>;
  if (!cfg) return <div className="glass-panel p-4">No config</div>;

  return (
    <div className="space-y-4">
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-white/90 font-semibold">Rotation Lab</div>
          <div className="flex items-center gap-2">
            <button onClick={save} disabled={saving} className="btn btn-outline text-xs py-1">{saving?'Saving…':'Save'}</button>
            <button onClick={reloadLive} className="btn btn-outline text-xs py-1">Recompute now</button>
            <button onClick={runBacktest} className="btn btn-outline text-xs py-1">Backtest</button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <NumberInput label="Capital" value={cfg.capital} onChange={v=>setCfg({...cfg, capital:v})} step={1000} hint="Total capital used for backtests and live allocation sizing." />
          <label className="block">
            <div className="text-xs text-gray-400 mb-1">Rebalance</div>
            <select value={cfg.rebalance} onChange={e=>setCfg({...cfg, rebalance:e.target.value})} className="form-input w-full">
              <option value="D">Daily</option>
              <option value="W">Weekly</option>
              <option value="M">Monthly</option>
            </select>
          </label>
          <NumberInput label="Trend days (200)" value={cfg.trend_days} onChange={v=>setCfg({...cfg, trend_days:v})} hint="200-day SMA regime filter (price above = bull regime, below = bear)." />
          <NumberInput label="EMA fast (20)" value={cfg.ema_fast} onChange={v=>setCfg({...cfg, ema_fast:v})} hint="Short EMA length used in DualUp (EMAfast > EMAslow)." />
          <NumberInput label="EMA slow (50)" value={cfg.ema_slow} onChange={v=>setCfg({...cfg, ema_slow:v})} hint="Long EMA length used in DualUp (EMAfast > EMAslow)." />
          <NumberInput label="RSI len (14)" value={cfg.rsi_len} onChange={v=>setCfg({...cfg, rsi_len:v})} hint="RSI period; >50 contributes to bull confirmations; <50 contributes to bear." />
          <NumberInput label="ATR len (20)" value={cfg.atr_len} onChange={v=>setCfg({...cfg, atr_len:v})} hint="ATR length used for Keltner bands (EMA20 ± mult × ATR)." />
          <NumberInput label="Keltner mult (2.0)" value={cfg.kelt_mult} onChange={v=>setCfg({...cfg, kelt_mult:v})} step={0.1} hint="Multiplier for ATR to set Keltner upper/lower bands (2.0 typical)." />
          <div className="grid grid-cols-3 gap-2">
            <NumberInput label="MACD fast" value={cfg.macd_fast} onChange={v=>setCfg({...cfg, macd_fast:v})} />
            <NumberInput label="MACD slow" value={cfg.macd_slow} onChange={v=>setCfg({...cfg, macd_slow:v})} />
            <NumberInput label="MACD signal" value={cfg.macd_signal} onChange={v=>setCfg({...cfg, macd_signal:v})} />
          </div>
          <NumberInput label="Consec DualUp days" value={cfg.consec_needed} onChange={v=>setCfg({...cfg, consec_needed:v})} />
          <NumberInput label="Conf threshold" value={cfg.conf_threshold} onChange={v=>setCfg({...cfg, conf_threshold:v})} />
          <label className="block">
            <div className="text-xs text-gray-400 mb-1">Execution</div>
            <select value={cfg.exec_timing} onChange={e=>setCfg({...cfg, exec_timing:e.target.value})} className="form-input w-full">
              <option value="next_open">Next-day open</option>
              <option value="close">Same-day close</option>
            </select>
          </label>
          <div className="grid grid-cols-2 gap-2">
            <NumberInput label="Costs (bps)" value={cfg.cost_bps} onChange={v=>setCfg({...cfg, cost_bps:v})} />
            <NumberInput label="Slippage (bps)" value={cfg.slippage_bps} onChange={v=>setCfg({...cfg, slippage_bps:v})} />
          </div>
        </div>
      </div>

      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-white/90 font-semibold">Pairs</div>
          <div className="flex items-center gap-2">
            <label className="btn btn-outline text-xs py-1 cursor-pointer">
              Upload XLSX
              <input type="file" className="hidden" accept=".xlsx,.xls" onChange={(e)=>{ if(e.target.files?.[0]) uploadXLSX(e.target.files[0]); }} />
            </label>
            <button onClick={()=>setCfg({...cfg, pairs:[...cfg.pairs, {bull:'TQQQ', bear:'SQQQ', underlying:'QQQ'}]})} className="btn btn-outline text-xs py-1">Add pair</button>
          </div>
        </div>
        <div className="space-y-2">
          {(cfg.pairs||[]).map((p, idx)=>(
            <div key={idx} className="grid grid-cols-1 md:grid-cols-6 gap-2 items-center">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-3"><div className="text-white/90 font-semibold">Live signals</div><button onClick={reloadLive} className="btn btn-outline text-xs py-1">Reload</button></div>
          <pre className="text-xs text-gray-300 overflow-auto max-h-64">{JSON.stringify(live, null, 2)}</pre>
        </div>
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-3"><div className="text-white/90 font-semibold">Backtest</div><button onClick={runBacktest} className="btn btn-outline text-xs py-1">Run</button></div>
          <pre className="text-xs text-gray-300 overflow-auto max-h-64">{JSON.stringify(bt, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
};

export default RotationLab;