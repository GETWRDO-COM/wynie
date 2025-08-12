import React from 'react';

const DashboardQuickSections = ({ swingLeaders, watchlists, marketScore }) => {
  return (
    <div className="space-y-4">
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
          <div className="flex items-center justify-between mb-2">
            <div className="text-white/90 font-semibold">Watchlists</div>
            <button onClick={() => window.location.hash = '#/watchlists'} className="btn btn-outline text-xs py-1">See more</button>
          </div>
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