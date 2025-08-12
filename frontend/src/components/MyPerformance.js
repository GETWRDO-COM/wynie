import React, { useEffect, useMemo, useState } from 'react';

const RANGES = [
  { id: '1D', label: '1D' },
  { id: '1W', label: '1W' },
  { id: '1M', label: '1M' },
  { id: 'YTD', label: 'YTD' },
  { id: '1Y', label: '1Y' },
];

const MyPerformance = ({ api }) => {
  const [range, setRange] = useState('1D');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async (r) => {
    setLoading(true); setError('');
    try {
      const resp = await api.get(`/api/portfolio/performance?range=${encodeURIComponent(r)}`);
      setData(resp.data);
    } catch (e) {
      setError('Not connected');
      setData(null);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(range); }, [range]);

  const updated = useMemo(() => {
    if (!data?.last_updated) return null;
    const dt = new Date(data.last_updated);
    return new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(dt);
  }, [data]);

  const Stat = ({ title, amount, change }) => (
    <div className="glass-panel p-4">
      <div className="text-xs text-gray-400 mb-1">{title}</div>
      <div className="text-2xl font-bold text-white">{amount != null ? `$${amount.toLocaleString(undefined,{minimumFractionDigits:2, maximumFractionDigits:2})}` : '--'}</div>
      <div className={`text-xs font-semibold ${change > 0 ? 'text-green-400' : change < 0 ? 'text-red-400' : 'text-gray-300'}`}>{change > 0 ? '+' : ''}{change != null ? change.toFixed(2) : '--'}%</div>
    </div>
  );

  const totalDelta = useMemo(() => {
    if (!data) return null;
    return typeof data.total_delta_amount === 'number' ? data.total_delta_amount : null;
  }, [data]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-white/90 font-semibold text-lg">My Performance</div>
        <div className="flex items-center gap-2">
          {RANGES.map((r) => (
            <button key={r.id} onClick={() => setRange(r.id)} className={`px-3 py-1.5 rounded-lg text-sm ${range===r.id?'text-white bg-white/10 border border-white/10':'text-gray-300 hover:text-white hover:bg-white/5'}`}>{r.label}</button>
          ))}
        </div>
        <div className="text-xs text-gray-400">{updated ? `Updated ${updated}` : ''}</div>
      </div>
      {error && <div className="text-xs text-amber-300">{error} — connect your trading dashboard to show live performance.</div>}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 items-stretch">
        <div className="glass-panel p-4 relative">
          <div className="absolute right-4 top-4 text-sm font-bold bg-white/10 text-white rounded px-2 py-1">{totalDelta != null ? `${totalDelta>0?'+':''}$${totalDelta.toLocaleString(undefined,{maximumFractionDigits:0})}` : ''}</div>
          <div className="text-xs text-gray-400 mb-1">Total</div>
          <div className="text-3xl font-extrabold text-white">{data?.total_amount != null ? `$${data.total_amount.toLocaleString(undefined,{minimumFractionDigits:2, maximumFractionDigits:2})}` : '--'}</div>
          <div className={`text-xs font-semibold ${data?.total_change_pct > 0 ? 'text-green-400' : data?.total_change_pct < 0 ? 'text-red-400' : 'text-gray-300'}`}>{data?.total_change_pct > 0 ? '+' : ''}{data?.total_change_pct != null ? data.total_change_pct.toFixed(2) : '--'}%</div>
        </div>
        <Stat title="Portfolio 1" amount={data?.portfolio1_amount} change={data?.portfolio1_change_pct} />
        <Stat title="Portfolio 2" amount={data?.portfolio2_amount} change={data?.portfolio2_change_pct} />
      </div>
    </div>
  );
};

export default MyPerformance;