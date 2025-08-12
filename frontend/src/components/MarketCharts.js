import React, { useEffect, useState } from 'react';
import { Line } from 'react-chartjs-2';

function rel(ts){ if(!ts) return ''; const d=(ts instanceof Date? ts.getTime(): new Date(ts).getTime()); const diff=Math.round((d-Date.now())/60000); const rtf=new Intl.RelativeTimeFormat('en',{numeric:'auto'}); if(Math.abs(diff)<60) return rtf.format(diff,'minute'); const dh=Math.round(diff/60); if(Math.abs(dh)<24) return rtf.format(dh,'hour'); const dd=Math.round(dh/24); return rtf.format(dd,'day'); }

const TICKERS = [ { id: 'SPY', label: 'SPY' }, { id: 'QQQ', label: 'QQQ' }, { id: 'I:DJI', label: 'DOW (DJI)' }, { id: 'TQQQ', label: 'TQQQ' }, { id: 'SQQQ', label: 'SQQQ' } ];
const RANGES = ['1D','1W','1M','YTD','1Y'];

const MarketCharts = () => {
  const [range, setRange] = useState('1M');
  const [data, setData] = useState({});
  const [updatedAt, setUpdatedAt] = useState(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const load = async (r) => {
    try { const tickers = TICKERS.map(t => t.id).join(','); const res = await fetch(`${BACKEND_URL}/api/market/aggregates?tickers=${encodeURIComponent(tickers)}&range=${encodeURIComponent(r)}`); const js = await res.json(); setData(js.data || {}); setUpdatedAt(js.last_updated ? new Date(js.last_updated) : new Date()); } catch (e) { console.error('Chart load failed', e); }
  };

  useEffect(() => { load(range); const id = setInterval(() => load(range), 5*60*1000); return () => clearInterval(id); }, [range]);

  const formatNumber = (x) => (x == null ? '--' : x.toFixed(2));

  return (
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-white/90 font-semibold">Market Snapshot</div>
        <div className="flex items-center gap-2"><button onClick={()=>load(range)} className="btn btn-outline text-xs py-1">Reload</button>
          {RANGES.map(r => (
            <button key={r} onClick={() => setRange(r)} className={`px-3 py-1.5 rounded-lg text-sm ${range===r?'text-white bg-white/10 border border-white/10':'text-gray-300 hover:text-white hover:bg-white/5'}`}>{r}</button>
          ))}
        </div>
        <div className="text-xs text-gray-400">Updated {rel(updatedAt)}</div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {TICKERS.map(t => {
          const td = data[t.id] || {}; const series = td.series || [];
          const labels = series.map(p => new Date(p.t).toLocaleDateString()); const values = series.map(p => p.c);
          const change = td.change_pct; const up = change != null ? change >= 0 : true;
          const color = up ? 'rgba(34,197,94,1)' : 'rgba(239,68,68,1)'; const fill = up ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)';
          const chartData = { labels, datasets: [{ label: t.label, data: values, borderColor: color, backgroundColor: fill, tension: 0.35, pointRadius: 0, fill: true, borderWidth: 2 }] };
          const options = {responsive: true, plugins:{legend:{display:false}, tooltip:{mode:'index', intersect:false}}, scales:{x:{display:false}, y:{display:false}}};
          const pre = td.pre_market, post = td.post_market, open = td.open;
          return (
            <div key={t.id} className="rounded-xl border border-white/10 bg-black/30 p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="text-white/90 font-semibold">{t.label}</div>
                <div className={`text-sm font-semibold ${up?'text-green-400':'text-red-400'}`}>{change==null?'--':(change>0?'+':'')+change.toFixed(2)+'%'}</div>
              </div>
              <div className="text-xs text-gray-400 mb-2">
                Open: <span className="text-white/90">{formatNumber(open)}</span> • Close: <span className="text-white/90">{formatNumber(td.close)}</span>
                {pre!=null && <> • Pre‑Mkt: <span className="text-white/90">{formatNumber(pre)}</span></>}
                {post!=null && <> • Post‑Mkt: <span className="text-white/90">{formatNumber(post)}</span></>}
              </div>
              <div className="h-32"><Line data={chartData} options={options} /></div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default MarketCharts;