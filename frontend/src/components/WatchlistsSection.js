import React, { useState, useEffect } from 'react';

const WatchlistsSection = () => {
  const [watchlists, setWatchlists] = useState([]);
  const [loading, setLoading] = useState(true);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const loadWatchlists = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/watchlists/custom`, {
        headers: (() => { 
          const token = localStorage.getItem('authToken'); 
          return token ? { Authorization: `Bearer ${token}` } : {}; 
        })()
      });
      
      if (response.ok) {
        const data = await response.json();
        setWatchlists(data.watchlists || []);
      }
    } catch (error) {
      console.error('Failed to load watchlists:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWatchlists();
  }, []);

  const formatChange = (change) => {
    if (!change) return '--';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const getChangeColor = (change) => {
    if (!change) return 'text-gray-400';
    return change >= 0 ? 'text-green-400' : 'text-red-400';
  };

  if (loading) {
    return (
      <div className="glass-panel p-6">
        <div className="text-white/90 font-semibold mb-4">Watchlists</div>
        <div className="text-gray-400 text-sm">Loading watchlists...</div>
      </div>
    );
  }

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-white/90 font-semibold">Watchlists</div>
        <a 
          href="#/watchlists" 
          className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          See More →
        </a>
      </div>

      {watchlists.length === 0 ? (
        <div className="text-gray-400 text-sm text-center py-8">
          <div className="mb-2">📋</div>
          <div>No watchlists created yet</div>
          <button className="mt-3 btn btn-outline text-xs">
            Create Watchlist
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {watchlists.slice(0, 3).map((watchlist) => (
            <div 
              key={watchlist.id}
              className="rounded-xl border border-white/10 bg-black/30 p-4 hover:bg-black/40 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="text-white/90 font-semibold">{watchlist.name}</div>
                <div className={`text-sm font-semibold ${getChangeColor(watchlist.performance?.daily_change)}`}>
                  {formatChange(watchlist.performance?.daily_change)}
                </div>
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-400">
                <div>{watchlist.tickers?.length || 0} stocks</div>
                <div>
                  {watchlist.performance?.total_value 
                    ? `$${watchlist.performance.total_value.toLocaleString()}` 
                    : '--'
                  }
                </div>
              </div>
              
              {watchlist.tickers && watchlist.tickers.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {watchlist.tickers.slice(0, 5).map((ticker) => (
                    <span 
                      key={ticker}
                      className="px-2 py-0.5 bg-white/10 text-white/80 text-xs rounded"
                    >
                      {ticker}
                    </span>
                  ))}
                  {watchlist.tickers.length > 5 && (
                    <span className="px-2 py-0.5 bg-white/5 text-gray-400 text-xs rounded">
                      +{watchlist.tickers.length - 5} more
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
          
          {watchlists.length > 3 && (
            <div className="text-center pt-2">
              <a 
                href="#/watchlists" 
                className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors"
              >
                View all {watchlists.length} watchlists →
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default WatchlistsSection;