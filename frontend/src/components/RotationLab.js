import React, { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';

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

const RotationLab = ({ api }) => {
  const [cfg, setCfg] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [live, setLive] = useState(null);
  const [bt, setBt] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [running, setRunning] = useState(false);

  useEffect(()=>{ (async()=>{ try{ const r = await api.get('/api/rotation/config'); setCfg(r.data.config || r.data); } finally { setLoading(false); } })(); }, [api]);

  const save = async()=>{ setSaving(true); try{ await api.post('/api/rotation/config', cfg); } finally { setSaving(false);} };
  const reloadLive = async()=>{ const r = await api.get('/api/rotation/live'); setLive(r.data); };
  const runBacktest = async()=>{ setRunning(true); try{ const r = await api.post('/api/rotation/backtest', cfg); setBt(r.data); } finally { setRunning(false);} };

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

  // Monthly heatmap
  const monthly = useMemo(()=>{
    if(!bt?.equity_curve?.length) return null;
    const parse = (s)=> new Date(s);
    // Last equity in each month
    const byMonth = new Map();
    bt.equity_curve.forEach(p=>{ const d=parse(p.date); const key=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; byMonth.set(key, p.equity); });
    // Sort keys
    const keys = Array.from(byMonth.keys()).sort();
    const rowsMap = new Map(); // year -> { month->ret }
    let prev = null; keys.forEach(k=>{ const [y,m] = k.split('-'); const eq = byMonth.get(k); if(prev!=null){ const ret = (eq/prev-1); const row = rowsMap.get(y) || {}; row[m]=ret; rowsMap.set(y,row); } prev = eq; });
    const years = Array.from(rowsMap.keys()).sort();
    const months = ['01','02','03','04','05','06','07','08','09','10','11','12'];
    return { years, months, rows: rowsMap };
  }, [bt]);

  const heatColor = (v)=>{
    if(v==null) return 'bg-white/5';
    // clamp -20%..+20%
    const x = Math.max(-0.2, Math.min(0.2, v));
    if(x>=0){ const g = Math.round(200 * (x/0.2)); return `bg-[rgba(34,197,94,${0.25+0.55*(x/0.2)})] text-white`; }
    const r = Math.round(200 * (-x/0.2)); return `bg-[rgba(239,68,68,${0.25+0.55*(-x/0.2)})] text-white`;
  };

  const exportEquityCSV = ()=>{
    if(!bt) return; const rows = (bt.equity_curve||[]).map((p,idx)=>({date:p.date, equity:p.equity, drawdown: bt.drawdown?.[idx]?.dd ?? ''}));
    download('rotation_equity.csv', toCSV(rows, ['date','equity','drawdown']));
  };
  const exportTradesCSV = ()=>{
    if(!bt) return; const rows = (bt.trades||[]).map(t=>({date:t.date, action:t.action, ticker:t.ticker, shares:t.shares, price:t.price}));
    download('rotation_trades.csv', toCSV(rows, ['date','action','ticker','shares','price']));
  };

  if (loading) return <div className="glass-panel p-4">Loading Rotation Lab…</div>;
  if (!cfg) return <div className="glass-panel p-4">No config</div>;

  return (
    <div className="space-y-4">
      <div className="glass-panel p-4">
        <div className="flex items-center justify-between mb-2">
          <div>
            <div className="text-xs text-gray-400">Strategy Workspace</div>
            <div className="text-white/90 font-semibold">Rotation Lab</div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={save} disabled={saving} className="btn btn-outline text-xs py-1">{saving?'Saving…':'Save'}</button>
            <button onClick={reloadLive} className="btn btn-outline text-xs py-1">Recompute now</button>
            <button onClick={runBacktest} disabled={running} className="btn btn-outline text-xs py-1">{running?'Running…':'Backtest'}</button>
          </div>
        </div>
        <div className="text-xs text-gray-400 mb-3">Tune parameters exactly like your spreadsheet. Hover the “i” for help.</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <NumberInput label="Capital" value={cfg.capital} onChange={v=>setCfg({...cfg, capital:v})} step={1000} hint="Total capital used for backtests and live allocation sizing." />
          <label className="block">
            <div className="text-xs text-gray-300 mb-1 flex items-center gap-1">Rebalance <Info text="Controls when allocations are refreshed. Backtest currently runs daily; weekly/monthly coming next." /></div>
            <select value={cfg.rebalance} onChange={e=>setCfg({...cfg, rebalance:e.target.value})} className="form-input w-full">
              <option value="D">Daily</option>
              <option value="W">Weekly</option>
              <option value="M">Monthly</option>
            </select>
          </label>
          <label className="block">
            <div className="text-xs text-gray-300 mb-1 flex items-center gap-1">Execution <Info text="Select whether trades execute same-day close (uses close) or next-day open (default)." /></div>
            <select value={cfg.exec_timing} onChange={e=>setCfg({...cfg, exec_timing:e.target.value})} className="form-input w-full">
              <option value="next_open">Next-day open</option>
              <option value="close">Same-day close</option>
            </select>
          </label>
          <NumberInput label="Trend days (200)" value={cfg.trend_days} onChange={v=>setCfg({...cfg, trend_days:v})} hint="200-day SMA regime filter (price above = bull regime, below = bear)." />
          <NumberInput label="EMA fast (20)" value={cfg.ema_fast} onChange={v=>setCfg({...cfg, ema_fast:v})} hint="Short EMA length used in DualUp (EMAfast > EMAslow)." />
          <NumberInput label="EMA slow (50)" value={cfg.ema_slow} onChange={v=>setCfg({...cfg, ema_slow:v})} hint="Long EMA length used in DualUp (EMAfast > EMAslow)." />
          <NumberInput label="RSI len (14)" value={cfg.rsi_len} onChange={v=>setCfg({...cfg, rsi_len:v})} hint="RSI period; >50 contributes to bull confirmations; <50 contributes to bear." />
          <NumberInput label="ATR len (20)" value={cfg.atr_len} onChange={v=>setCfg({...cfg, atr_len:v})} hint="ATR length used for Keltner bands (EMA20 ± mult × ATR)." />
          <NumberInput label="Keltner mult (2.0)" value={cfg.kelt_mult} onChange={v=>setCfg({...cfg, kelt_mult:v})} step={0.1} hint="Multiplier for ATR to set Keltner upper/lower bands (2.0 typical)." />
          <div className="grid grid-cols-3 gap-2">
            <NumberInput label="MACD fast" value={cfg.macd_fast} onChange={v=>setCfg({...cfg, macd_fast:v})} hint="Standard MACD parameters; bullish when MACD line > signal." />
            <NumberInput label="MACD slow" value={cfg.macd_slow} onChange={v=>setCfg({...cfg, macd_slow:v})} />
            <NumberInput label="MACD signal" value={cfg.macd_signal} onChange={v=>setCfg({...cfg, macd_signal:v})} />
          </div>
          <NumberInput label="Consec DualUp days" value={cfg.consec_needed} onChange={v=>setCfg({...cfg, consec_needed:v})} hint="Minimum consecutive days with EMAfast>EMAslow required before a long entry (reduces whipsaws)." />
          <NumberInput label="Conf threshold" value={cfg.conf_threshold} onChange={v=>setCfg({...cfg, conf_threshold:v})} hint="How many bullish confirmations required (DualUp, Trend>200DMA, Kelt>upper, MACD bull, RSI>50)." />
          <div className="grid grid-cols-2 gap-2">
            <NumberInput label="Costs (bps)" value={cfg.cost_bps} onChange={v=>setCfg({...cfg, cost_bps:v})} hint="Commission and fees per trade, in basis points." />
            <NumberInput label="Slippage (bps)" value={cfg.slippage_bps} onChange={v=>setCfg({...cfg, slippage_bps:v})} hint="Assumed slippage per trade, in basis points." />
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

      {bt && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
          <div className="glass-panel p-4 xl:col-span-2">
            <div className="flex items-center justify-between mb-3">
              <div className="text-white/90 font-semibold">Equity Curve</div>
              <div className="flex items-center gap-2">
                <button onClick={exportEquityCSV} className="btn btn-outline text-xs py-1">Export CSV</button>
              </div>
            </div>
            {equityData ? (<div className="h-64"><Line data={equityData} options={{responsive:true, plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:true, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Run a backtest to see results.</div>)}
          </div>
          <div className="glass-panel p-4">
            <div className="text-white/90 font-semibold mb-3">Drawdown</div>
            {ddData ? (<div className="h-64"><Line data={ddData} options={{responsive:true, plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:true, ticks:{color:'#cbd5e1'}}}}} /></div>) : (<div className="text-xs text-gray-400">Run a backtest.</div>)}
          </div>
        </div>
      )}

      {bt && monthly && (
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-white/90 font-semibold">Monthly Returns Heatmap</div>
            <button onClick={exportEquityCSV} className="btn btn-outline text-xs py-1">Export Equity CSV</button>
          </div>
          <div className="overflow-auto">
            <table className="min-w-[640px] text-xs">
              <thead>
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
                      <td className="px-2 py-1 text-gray-400">{y}</td>
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

      {bt && (
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-white/90 font-semibold">Trades</div>
            <button onClick={exportTradesCSV} className="btn btn-outline text-xs py-1">Export CSV</button>
          </div>
          <div className="overflow-auto max-h-80">
            <table className="min-w-[560px] text-xs">
              <thead>
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
    </div>
  );
};

export default RotationLab;