import React, { useEffect, useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';

const GreedFearCard = () => {
  const [data, setData] = useState(null);
  const [updatedAt, setUpdatedAt] = useState(null);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const load = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/greed-fear`);
      const js = await res.json();
      setData(js);
      setUpdatedAt(js.last_updated ? new Date(js.last_updated) : new Date());
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => { load(); const id = setInterval(load, 6*60*60*1000); return () => clearInterval(id); }, []);

  const spark = useMemo(() => {
    const series = (data && (data.timeseries || [])).slice(-60); // last 60 points if present
    if (!series || !series.length) return null;
    const labels = series.map((p, i) => i + 1);
    const values = series.map((p) => (typeof p === 'number' ? p : (p.value || p.score || 0)));
    return {
      labels,
      datasets: [{ data: values, borderColor: 'rgba(255,255,255,0.9)', backgroundColor: 'rgba(255,255,255,0.08)', tension: 0.25, pointRadius: 0, fill: true }]
    };
  }, [data]);

  const updated = updatedAt ? new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(updatedAt) : '--:--';

  const now = data?.now ?? null;
  const prev = data?.previous_close ?? null;
  const w = data?.one_week_ago ?? null;
  const m = data?.one_month_ago ?? null;
  const y = data?.one_year_ago ?? null;

  return (
    <div className="rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <img src="https://asset.brandfetch.io/idTxxrVf-x/idU4vcfJSP.svg" alt="CNN" className="h-5" />
          <div className="text-white/90 font-semibold">Fear & Greed Index</div>
        </div>
        <div className="text-xs text-gray-400">Updated {updated}</div>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center justify-center w-20 h-20 rounded-full border-2 border-white/20 bg-white/5">
          <div className="text-2xl font-bold text-white">{now ?? '--'}</div>
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