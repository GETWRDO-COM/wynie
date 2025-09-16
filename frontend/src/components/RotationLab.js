import React, { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';

// Simple, prominent info icon with tooltip
function Info({text}){
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex items-center">
      <button type="button" onMouseEnter={()=>setOpen(true)} onMouseLeave={()=>setOpen(false)} onFocus={()=>setOpen(true)} onBlur={()=>setOpen(false)} className="inline-flex items-center justify-center w-4 h-4 rounded-full border border-white/30 text-[10px] text-white/90 bg-white/10 hover:bg-white/20 shadow-[0_0_12px_rgba(0,255,255,0.25)] ml-1 align-middle">i</button>
      {open && (
        <div className="absolute z-50 top-5 left-1/2 -translate-x-1/2 min-w-[220px] max-w-[320px] text-xs text-white bg-black/90 border border-white/15 rounded-lg p-2 shadow-xl">
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

const PRESETS = {
  'Sheet: Keltner + EMA + 200DMA': {
    ema_fast: 20, ema_slow: 50, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 2, conf_threshold: 2, exec_timing: 'next_open',
    cost_bps: 5, slippage_bps: 5
  },
  'Sheet: DMA 50/200 (no Keltner)': {
    ema_fast: 50, ema_slow: 200, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 2, conf_threshold: 2, exec_timing: 'next_open',
    cost_bps: 5, slippage_bps: 5
  },
  'Conservative (more confirm)': {
    ema_fast: 20, ema_slow: 50, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 3, conf_threshold: 3, exec_timing: 'next_open',
    cost_bps: 5, slippage_bps: 5
  },
  'Aggressive (faster entries)': {
    ema_fast: 20, ema_slow: 50, trend_days: 200,
    rsi_len: 14, atr_len: 20, kelt_mult: 2.0,
    macd_fast: 12, macd_slow: 26, macd_signal: 9,
    consec_needed: 1, conf_threshold: 2, exec_timing: 'close',
    cost_bps: 5, slippage_bps: 5
  }
};

const RotationLab = ({ api }) => {
  const [cfg, setCfg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [live, setLive] = useState(null);
  const [bt, setBt] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);
  const [preset, setPreset] = useState('Sheet: Keltner + EMA + 200DMA');

  // Compare A/B
  const [compA, setCompA] = useState(null);
  const [compB, setCompB] = useState(null);
  const [resA, setResA] = useState(null);
  const [resB, setResB] = useState(null);
  const [comparing, setComparing] = useState(false);

  useEffect(()=>{ (async()=>{ try{ const r = await api.get('/api/rotation/config'); setCfg(r.data.config || r.data); } finally { setLoading(false); } })(); }, [api]);

  const applyPreset = (key)=>{
    if(!cfg) return;
    const p = PRESETS[key];
    if(!p) return;
    // keep pairs if already defined, else default
    const pairs = (cfg.pairs && cfg.pairs.length) ? cfg.pairs : [{bull:'TQQQ', bear:'SQQQ', underlying:'QQQ'}];
    setCfg({...cfg, ...p, pairs});
    setPreset(key);
  };

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
    } catch(e){
      alert('Upload failed');
    } finally { setUploading(false); }
  };

  const runCompare = async()=>{
    if(!compA || !compB) { alert('Set both A and B from current or presets.'); return; }
    setComparing(true);
    try{
      const [ra, rb] = await Promise.all([
        api.post('/api/rotation/backtest', compA),
        api.post('/api/rotation/backtest', compB),
      ]);
      setResA(ra.data); setResB(rb.data);
    } finally { setComparing(false); }
  };

  // Prepare charts from backtest
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

  const exportEquityCSV = ()=>{
    if(!bt) return; const rows = (bt.equity_curve||[]).map((p,idx)=>({date:p.date, equity:p.equity, drawdown: bt.drawdown?.[idx]?.dd ?? ''}));
    download('rotation_equity.csv', toCSV(rows, ['date','equity','drawdown']));
  };
  const exportTradesCSV = ()=>{
    if(!bt) return; const rows = (bt.trades||[]).map(t=>({date:t.date, action:t.action, ticker:t.ticker, shares:t.shares, price:t.price}));
    download('rotation_trades.csv', toCSV(rows, ['date','action','ticker','shares','price']));
  };

  const Metric = ({label, value, hint, color='text-white'})=> (
    <div className="rounded-xl bg-black/30 border border-white/10 p-3">
      <div className="text-[11px] text-gray-400 flex items-center gap-1">{label}<Info text={hint} /></div>
      <div className={`text-2xl font-extrabold ${color}`}>{value}</div>
    </div>
  );

  if (loading) return <div className="glass-panel p-4">Loading Rotation Lab…</div>;
  if (!cfg) return <div className="glass-panel p-4">No config</div>;

  // Compute KPI values for primary backtest
  const kpi = bt?.metrics || null;
  const fmtPct = (x)=> x==null? '--' : (x*100).toFixed(2)+'%';
  const fmt = (x)=> x==null? '--' : Number(x).toFixed(2);

  return (
    <div className="space-y-4" key="rotation-v2-20250612">
      {/* Hero header */}
      <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-[#0b0f1a]/80 to-[#0c1222]/80 backdrop-blur-xl p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-xs text-cyan-300/80 mb-1">Strategy Workspace</div>
            <div className="text-white font-extrabold text-2xl sm:text-3xl">Rotation Lab</div>
            <div className="text-sm text-gray-300 mt-1">Select a preset or set your own rules, run a backtest, then review performance and trades.</div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <label className="text-xs text-gray-300">Preset</label>
            <div className="flex items-center gap-2">
              <select value={preset} onChange={(e)=>applyPreset(e.target.value)} className="form-input text-sm">
                {Object.keys(PRESETS).map(k=> <option key={k} value={k}>{k}</option>)}
              </select>
              <button onClick={()=>setCompA({...cfg})} className="btn btn-outline text-xs py-1" title="Set A from current">Set A</button>
              <button onClick={()=>setCompB({...cfg})} className="btn btn-outline text-xs py-1" title="Set B from current">Set B</button>
            </div>
          </div>
        </div>
        <div className="mt-3 text-[11px] text-gray-400">How it works: 1) Choose a preset or adjust settings. 2) Add your pairs (TQQQ/SQQQ on QQQ). 3) Click Backtest. 4) Review KPIs, charts, heatmap, and trades. 5) Export CSVs or compare A/B.</div>
      </div>

      {/* Configuration */}
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-white/90 font-semibold">Configuration</div>
            <div className="text-xs text-gray-400">Define signal lengths, regime filters, and execution.</div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={save} disabled={saving} className="btn btn-outline text-xs py-1">{saving?'Saving…':'Save'}</button>
            <button onClick={reloadLive} className="btn btn-outline text-xs py-1">Recompute now</button>
            <button onClick={runBacktest} disabled={running} className="btn btn-outline text-xs py-1">{running?'Running…':'Backtest'}</button>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <NumberInput label="Capital" value={cfg.capital} onChange={v=>setCfg({...cfg, capital:v})} step={1000} hint="Total capital used for backtests and live allocation sizing." />
          <label className="block">
            <div className="text-xs text-gray-300 mb-1 flex items-center gap-1">Rebalance<Info text="Controls when allocations are refreshed. Backtest currently runs daily; weekly/monthly supported for rotation timing." /></div>
            <select value={cfg.rebalance} onChange={e=>setCfg({...cfg, rebalance:e.target.value})} className="form-input w-full">
              <option value="D">Daily</option>
              <option value="W">Weekly</option>
              <option value="M">Monthly</option>
            </select>
          </label>
          <label className="block">
            <div className="text-xs text-gray-300 mb-1 flex items-center gap-1">Execution Timing<Info text="Select whether trades execute same-day close (uses close) or next-day open (default)." /></div>
            <select value={cfg.exec_timing} onChange={e=>setCfg({...cfg, exec_timing:e.target.value})} className="form-input w-full">
              <option value="next_open">Next-day open</option>
              <option value="close">Same-day close</option>
            </select>
          </label>
          <NumberInput label="Trend Days (200)" value={cfg.trend_days} onChange={v=>setCfg({...cfg, trend_days:v})} hint="200-day SMA regime filter (price above = bull regime, below = bear)." />
          <NumberInput label="EMA Fast (20)" value={cfg.ema_fast} onChange={v=>setCfg({...cfg, ema_fast:v})} hint="Short EMA length used in DualUp (EMAfast > EMAslow)." />
          <NumberInput label="EMA Slow (50)" value={cfg.ema_slow} onChange={v=>setCfg({...cfg, ema_slow:v})} hint="Long EMA length used in DualUp (EMAfast > EMAslow)." />
          <NumberInput label="RSI Length (14)" value={cfg.rsi_len} onChange={v=>setCfg({...cfg, rsi_len:v})} hint="RSI period; >50 contributes to bull confirmations; <50 contributes to bear." />
          <NumberInput label="ATR Length (20)" value={cfg.atr_len} onChange={v=>setCfg({...cfg, atr_len:v})} hint="ATR length used for Keltner bands (EMA20 ± mult × ATR)." />
          <NumberInput label="Keltner Multiplier (2.0)" value={cfg.kelt_mult} onChange={v=>setCfg({...cfg, kelt_mult:v})} step={0.1} hint="Multiplier for ATR to set Keltner upper/lower bands (2.0 typical)." />
          <div className="grid grid-cols-3 gap-2">
            <NumberInput label="MACD Fast" value={cfg.macd_fast} onChange={v=>setCfg({...cfg, macd_fast:v})} hint="Standard MACD parameters; bullish when MACD line > signal." />
            <NumberInput label="MACD Slow" value={cfg.macd_slow} onChange={v=>setCfg({...cfg, macd_slow:v})} />
            <NumberInput label="MACD Signal" value={cfg.macd_signal} onChange={v=>setCfg({...cfg, macd_signal:v})} />
          </div>
          <NumberInput label="Consecutive DualUp Days" value={cfg.consec_needed} onChange={v=>setCfg({...cfg, consec_needed:v})} hint="Minimum consecutive days with EMAfast>EMAslow required before a long entry (reduces whipsaws)." />
          <NumberInput label="Confirmation Threshold" value={cfg.conf_threshold} onChange={v=>setCfg({...cfg, conf_threshold:v})} hint="How many bullish confirmations required (DualUp, Trend>200DMA, Kelt>upper, MACD bull, RSI>50)." />
          <div className="grid grid-cols-2 gap-2">
            <NumberInput label="Costs (bps)" value={cfg.cost_bps} onChange={v=>setCfg({...cfg, cost_bps:v})} hint="Commission and fees per trade, in basis points." />
            <NumberInput label="Slippage (bps)" value={cfg.slippage_bps} onChange={v=>setCfg({...cfg, slippage_bps:v})} hint="Assumed slippage per trade, in basis points." />
          </div>
        </div>
      </div>

      {/* Universe & Pairs */}
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-white/90 font-semibold">Universe & Pairs</div>
            <div className="text-xs text-gray-400">Specify the leveraged pair to trade, and the underlying used for signals (e.g., TQQQ/SQQQ on QQQ).</div>
          </div>
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

      {/* KPI Summary */}
      {kpi && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Metric label="CAGR" value={fmtPct(kpi.cagr)} hint="Compound Annual Growth Rate of the equity curve." color="text-emerald-300" />
          <Metric label="Max Drawdown" value={fmtPct(kpi.max_dd)} hint="Worst peak-to-trough loss." color="text-rose-300" />
          <Metric label="Sharpe" value={fmt(kpi.sharpe)} hint="Risk-adjusted return (assumes daily returns, 0% rf)." color="text-cyan-300" />
          <Metric label="Total Return" value={fmtPct(kpi.total_return)} hint="Overall return from start to end." color="text-indigo-300" />
        </div>
      )}

      {/* Charts */}
      {bt && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
          <div className="glass-panel p-4 xl:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <div>
                <div className="text-white/90 font-semibold">Equity Curve</div>
                <div className="text-xs text-gray-400">Portfolio value over time.</div>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={exportEquityCSV} className="btn btn-outline text-xs py-1">Export CSV</button>
              </div>
            </div>
            {equityData ? (<div className="h-64"><Line data={equityData} options={{responsive:true, plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:true, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Run a backtest to see results.</div>)}
          </div>
          <div className="glass-panel p-4">
            <div className="text-white/90 font-semibold mb-1">Drawdown</div>
            <div className="text-xs text-gray-400 mb-2">Peak-to-trough losses as percentage.</div>
            {ddData ? (<div className="h-64"><Line data={ddData} options={{responsive:true, plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:true, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Run a backtest.</div>)}
          </div>
        </div>
      )}

      {/* Monthly Heatmap */}
      {bt && monthly && (
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-white/90 font-semibold">Monthly Returns Heatmap</div>
              <div className="text-xs text-gray-400">End-of-month returns based on equity curve.</div>
            </div>
            <button onClick={exportEquityCSV} className="btn btn-outline text-xs py-1">Export Equity CSV</button>
          </div>
          <div className="overflow-auto max-h-80">
            <table className="min-w-[640px] text-xs">
              <thead className="sticky top-0 bg-black/70 backdrop-blur z-10">
                <tr>
                  <th className="px-2 py-1 text-left text-gray-400">Year</th>
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
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="text-white/90 font-semibold">Trades</div>
              <div className="text-xs text-gray-400">Executed buys and sells with size and price.</div>
            </div>
            <button onClick={exportTradesCSV} className="btn btn-outline text-xs py-1">Export CSV</button>
          </div>
          <div className="overflow-auto max-h-80">
            <table className="min-w-[560px] text-xs">
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
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-white/90 font-semibold">A/B Compare</div>
            <div className="text-xs text-gray-400">Compare two configurations side-by-side. Set A/B from current (or from presets), then run.</div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={()=>setCompA({...cfg, _label:'A'})} className="btn btn-outline text-xs py-1">Set A from current</button>
            <button onClick={()=>setCompB({...cfg, _label:'B'})} className="btn btn-outline text-xs py-1">Set B from current</button>
            <button onClick={runCompare} disabled={comparing} className="btn btn-outline text-xs py-1">{comparing? 'Comparing…':'Run Compare'}</button>
          </div>
        </div>
        {(resA || resB) ? (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
            <div className="rounded-2xl border border-white/10 bg-black/30 p-3 xl:col-span-3">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Metric label="A CAGR" value={fmtPct(resA?.metrics?.cagr)} hint="CAGR for A." color="text-indigo-300" />
                <Metric label="A Max DD" value={fmtPct(resA?.metrics?.max_dd)} hint="Max Drawdown for A." color="text-rose-300" />
                <Metric label="A Sharpe" value={fmt(resA?.metrics?.sharpe)} hint="Sharpe for A." color="text-cyan-300" />
                <Metric label="A Total Return" value={fmtPct(resA?.metrics?.total_return)} hint="Total Return for A." color="text-emerald-300" />
                <Metric label="B CAGR" value={fmtPct(resB?.metrics?.cagr)} hint="CAGR for B." color="text-indigo-300" />
                <Metric label="B Max DD" value={fmtPct(resB?.metrics?.max_dd)} hint="Max Drawdown for B." color="text-rose-300" />
                <Metric label="B Sharpe" value={fmt(resB?.metrics?.sharpe)} hint="Sharpe for B." color="text-cyan-300" />
                <Metric label="B Total Return" value={fmtPct(resB?.metrics?.total_return)} hint="Total Return for B." color="text-emerald-300" />
              </div>
            </div>
            <div className="glass-panel p-4 xl:col-span-2">
              <div className="text-white/90 font-semibold mb-2">Equity Overlay</div>
              {overlayEq ? (<div className="h-64"><Line data={overlayEq} options={{responsive:true, plugins:{legend:{display:true, labels:{color:'#cbd5e1'}}}, scales:{x:{display:false}, y:{display:true, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Set A & B, then run compare.</div>)}
            </div>
            <div className="glass-panel p-4">
              <div className="text-white/90 font-semibold mb-2">Drawdown Overlay</div>
              {overlayDD ? (<div className="h-64"><Line data={overlayDD} options={{responsive:true, plugins:{legend:{display:true, labels:{color:'#cbd5e1'}}}, scales:{x:{display:false}, y:{display:true, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Set A & B, then run compare.</div>)}
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400">Set A and B, then click Run Compare to see overlay charts and KPIs.</div>
        )}
      </div>
    </div>
  );
};

export default RotationLab;