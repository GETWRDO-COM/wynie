import React from 'react';
import { Line } from 'react-chartjs-2';

const MiniChart = ({ title, data }) => {
  if (!data || !data.dates || !data.prices) return null;
  const chartData = { labels: data.dates, datasets: [{ data: data.prices, borderColor: 'rgb(59, 130, 246)', backgroundColor: 'rgba(59,130,246,0.15)', tension: 0.25, borderWidth: 2, fill: true }] };
  const options = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } };
  return (
    <div className="glass-panel p-4">
      <div className="text-xs text-gray-400 mb-1">{title}</div>
      <div className="h-24"><Line data={chartData} options={options} /></div>
    </div>
  );
};

const DashboardQuickSections = ({ chartData, swingLeaders, watchlists, marketScore }) => {
  const indices = chartData || {};
  const updated = marketScore?.last_updated ? new Date(marketScore.last_updated) : null;
  const updatedFmt = updated ? new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' }).format(updated) : null;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-white/90 font-semibold text-lg">Market Snapshot</div>
        {updatedFmt && <div className="text-xs text-gray-400">Updated {updatedFmt}</div>}
      </div>
      {/* Indices */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <MiniChart title="S&P 500" data={indices.sp500 || indices.SPY} />
        <MiniChart title="NASDAQ 100" data={indices.nasdaq100 || indices.QQQ} />
        <MiniChart title="Dow Jones" data={indices.dowjones || indices.DIA} />
        <div className="glass-panel p-4">
          <div className="text-xs text-gray-400 mb-1">Market Score</div>
          <div className="text-2xl font-bold text-white">{marketScore?.score ?? '--'}</div>
          <div className="text-xs text-gray-400">Trend: {marketScore?.trend ?? 'N/A'}</div>
        </div>
      </div>

      {/* Swing Leaders + Watchlists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <div className="glass-panel p-4">
          <div className="text-white/90 font-semibold mb-2">Top Swing Leaders</div>
          <div className="divide-y divide-white/10">
            {(swingLeaders || []).slice(0, 6).map((it) => (
              <div key={it.ticker} className="py-2 flex items-center gap-3">
                <div className="w-12 font-bold text-white">{it.ticker}</div>
                <div className="flex-1 text-sm text-gray-300 truncate">{it.name}</div>
                <div className={`text-sm font-semibold ${it.change_1m > 0 ? 'text-green-400' : 'text-red-400'}`}>{it.change_1m > 0 ? '+' : ''}{(it.change_1m ?? 0).toFixed(2)}%</div>
              </div>
            ))}
            {(!swingLeaders || swingLeaders.length === 0) && <div className="py-6 text-sm text-gray-400">No leaders available.</div>}
          </div>
        </div>
        <div className="glass-panel p-4">
          <div className="text-white/90 font-semibold mb-2">Watchlists</div>
          <div className="grid grid-cols-2 gap-2">
            {(watchlists || []).slice(0, 6).map((wl) => (
              <div key={wl.id || wl.name} className="bg-white/5 border border-white/10 rounded-lg p-3">
                <div className="text-white font-semibold text-sm">{wl.name}</div>
                <div className="text-xs text-gray-400">{(wl.stocks?.length || 0)} stocks</div>
              </div>
            ))}
            {(!watchlists || watchlists.length === 0) && <div className="text-sm text-gray-400">No watchlists yet.</div>}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardQuickSections;