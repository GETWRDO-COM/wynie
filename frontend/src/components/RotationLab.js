import React, { useEffect, useMemo, useState } from 'react';

function NumberInput({label, value, onChange, step=1, min=0}){
  return (
    <label className="block">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <input type="number" value={value} onChange={e=>onChange(parseFloat(e.target.value))} step={step} min={min} className="form-input w-full" />
    </label>
  );
}

const RotationLab = ({ api }) => {
  const [cfg, setCfg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [live, setLive] = useState(null);
  const [bt, setBt] = useState(null);

  useEffect(()=>{ (async()=>{ try{ const r = await api.get('/api/rotation/config'); setCfg(r.data.config || r.data); } finally { setLoading(false); } })(); }, [api]);

  const save = async()=>{ setSaving(true); try{ await api.post('/api/rotation/config', cfg); } finally { setSaving(false);} };
  const reloadLive = async()=>{ const r = await api.get('/api/rotation/live'); setLive(r.data); };
  const runBacktest = async()=>{ const r = await api.post('/api/rotation/backtest', cfg); setBt(r.data); };

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
          <NumberInput label="Capital" value={cfg.capital} onChange={v=>setCfg({...cfg, capital:v})} step={1000} />
          <label className="block">
            <div className="text-xs text-gray-400 mb-1">Rebalance</div>
            <select value={cfg.rebalance} onChange={e=>setCfg({...cfg, rebalance:e.target.value})} className="form-input w-full">
              <option value="D">Daily</option>
              <option value="W">Weekly</option>
              <option value="M">Monthly</option>
            </select>
          </label>
          <NumberInput label="Lookback days" value={cfg.lookback_days} onChange={v=>setCfg({...cfg, lookback_days:v})} />
          <NumberInput label="Trend days" value={cfg.trend_days} onChange={v=>setCfg({...cfg, trend_days:v})} />
          <NumberInput label="Max positions" value={cfg.max_positions} onChange={v=>setCfg({...cfg, max_positions:v})} />
          <div className="grid grid-cols-2 gap-2">
            <NumberInput label="Costs (bps)" value={cfg.cost_bps} onChange={v=>setCfg({...cfg, cost_bps:v})} />
            <NumberInput label="Slippage (bps)" value={cfg.slippage_bps} onChange={v=>setCfg({...cfg, slippage_bps:v})} />
          </div>
        </div>
      </div>

      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="text-white/90 font-semibold">Pairs</div>
          <button onClick={()=>setCfg({...cfg, pairs:[...cfg.pairs, {bull:'TQQQ', bear:'SQQQ'}]})} className="btn btn-outline text-xs py-1">Add pair</button>
        </div>
        <div className="space-y-2">
          {(cfg.pairs||[]).map((p, idx)=>(
            <div key={idx} className="grid grid-cols-1 md:grid-cols-5 gap-2 items-center">
              <label className="block md:col-span-2"><div className="text-xs text-gray-400 mb-1">Bull</div><input value={p.bull} onChange={e=>{ const arr=[...cfg.pairs]; arr[idx]={...arr[idx], bull:e.target.value}; setCfg({...cfg, pairs:arr}); }} className="form-input w-full"/></label>
              <label className="block md:col-span-2"><div className="text-xs text-gray-400 mb-1">Bear</div><input value={p.bear} onChange={e=>{ const arr=[...cfg.pairs]; arr[idx]={...arr[idx], bear:e.target.value}; setCfg({...cfg, pairs:arr}); }} className="form-input w-full"/></label>
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