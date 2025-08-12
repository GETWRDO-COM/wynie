import React, { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';

function rel(ts){ if(!ts) return ''; const d=new Date(ts).getTime(); const diff=Math.round((d-Date.now())/60000); const rtf=new Intl.RelativeTimeFormat('en',{numeric:'auto'}); if(Math.abs(diff)<60) return rtf.format(diff,'minute'); const dh=Math.round(diff/60); if(Math.abs(dh)<24) return rtf.format(dh,'hour'); const dd=Math.round(dh/24); return rtf.format(dd,'day'); }
function colorForScore(score){ if(score == null) return '#9ca3af'; if(score <= 33) return '#ef4444'; if(score <= 66) return '#f59e0b'; return '#22c55e'; }
function emojiForScore(score){ if(score == null) return '😐'; if(score <= 33) return '😨'; if(score <= 66) return '😐'; return '😄'; }

const GreedFearCard = () => {
  const [data, setData] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const load = async () => { try { const res = await fetch(`${BACKEND_URL}/api/greed-fear`); const js = await res.json(); setData(js); setUpdatedAt(js.last_updated ? new Date(js.last_updated) : new Date()); } catch (e) {} };

  useEffect(() => { load(); const id = setInterval(load, 6*60*60*1000); return () => clearInterval(id); }, []);

  const spark = useMemo(() => { const ts = data?.timeseries; if(!ArrayList || !Array.isArray(ts)) return null; const series = ts.slice(-60); if(!series.length) return null; const labels = series.map((_, i) => i+1); const values = series.map((p) => (typeof p === 'number' ? p : (p.value || p.score || 0))); return { labels, datasets:[{ data: values, borderColor: 'rgba(255,255,255,0.9)', backgroundColor: 'rgba(255,255,255,0.08)', tension: 0.25, pointRadius: 0, fill: true }] }; }, [data]);

  const now = data?.now ?? null; const prev = data?.previous_close ?? null; const w = data?.one_week_ago ?? null; const m = data?.one_month_ago ?? null; const y = data?.one_year_ago ?? null;
  const circleColor = colorForScore(now); const face = emojiForScore(now);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <img src="https://logo.clearbit.com/cnn.com" alt="CNN" className="h-7 w-auto" />
          <div className="text-white/90 font-semibold">Fear & Greed Sentiment</div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>Updated {rel(updatedAt)}</span>
          <button onClick={load} className="btn btn-outline text-[10px] py-0.5 px-2">Reload</button>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="relative flex items-center justify-center w-20 h-20 rounded-full" style={{ background: 'rgba(255,255,255,0.06)', border: '2px solid rgba(255,255,255,0.2)'}}>
          <svg width="76" height="76" className="absolute">
            <circle cx="38" cy="38" r="32" stroke="#1f2937" strokeWidth="6" fill="none" />
            <circle cx="38" cy="38" r="32" stroke={circleColor} strokeWidth="6" fill="none" strokeLinecap="round" strokeDasharray={Math.max(10, Math.min(200, (now||0)/100*200)) + ", 220"} transform="rotate(-90 38 38)" />
          </svg>
          <div className="text-xl font-bold text-white z-10">{now ?? '--'}</div>
          <div className="absolute -right-2 -top-2 text-lg" title={now!=null?`${now}`:''}>{face}</div>
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs text-gray-300">
          {prev != null && <div>Prev close: <span className="text-white/90 font-medium">{prev}</span></div>}
          {w != null && <div>1 week ago: <span className="text-white/90 font-medium">{w}</span></div>}
          {m != null && <div>1 month ago: <span className="text-white/90 font-medium">{m}</span></div>}
          {y != null && <div>1 year ago: <span className="text-white/90 font-medium">{y}</span></div>}
        </div>
      </div>
      {spark && (
        <div className="mt-3 h-16">
          <Line data={spark} options={{ responsive: true, plugins: { legend: { display: false }, tooltip: { enabled: false } }, scales: { x: { display: false }, y: { display: false } } }} />
        </div>
      )}
    </div>
  );
};

export default GreedFearCard;