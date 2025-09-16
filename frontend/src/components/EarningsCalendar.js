import React, { useState, useEffect } from 'react';

const EarningsCalendar = () => {
  const [earnings, setEarnings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('All Earnings');
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const filters = ['My Watchlists', 'My Portfolio', 'All Earnings'];

  const loadEarnings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/earnings`, {
        headers: (() => { 
          const token = localStorage.getItem('authToken'); 
          return token ? { Authorization: `Bearer ${token}` } : {}; 
        })()
      });
      
      if (response.ok) {
        const data = await response.json();
        setEarnings(data.earnings || []);
      }
    } catch (error) {
      console.error('Failed to load earnings:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEarnings();
  }, []);

  const groupEarningsByDate = (earnings) => {
    const grouped = earnings.reduce((acc, earning) => {
      const date = earning.date;
      if (!acc[date]) {
        acc[date] = [];
      }
      acc[date].push(earning);
      return acc;
    }, {});

    // Sort dates
    const sortedDates = Object.keys(grouped).sort();
    return sortedDates.map(date => ({
      date,
      earnings: grouped[date].sort((a, b) => a.ticker.localeCompare(b.ticker))
    }));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(today.getDate() + 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
      return 'Tomorrow';
    } else {
      return date.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  const getSurpriseColor = (surprise) => {
    if (!surprise) return 'text-gray-400';
    return surprise >= 0 ? 'text-green-400' : 'text-red-400';
  };

  const getSurpriseIcon = (surprise) => {
    if (!surprise) return '—';
    return surprise >= 0 ? '↗' : '↘';
  };

  const getTimeColor = (time) => {
    return time === 'BMO' ? 'text-blue-400' : 'text-purple-400';
  };

  const groupedEarnings = groupEarningsByDate(earnings);

  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="text-white/90 font-semibold">Earnings Calendar</div>
        <button 
          onClick={loadEarnings}
          className="btn btn-outline text-xs py-1"
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Reload'}
        </button>
      </div>

      {/* Filter Options */}
      <div className="flex gap-2 mb-4">
        {filters.map((filterOption) => (
          <button
            key={filterOption}
            onClick={() => setFilter(filterOption)}
            className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
              filter === filterOption
                ? 'text-white bg-white/10 border border-white/10'
                : 'text-gray-300 hover:text-white hover:bg-white/5 border border-transparent'
            }`}
          >
            {filterOption}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm text-center py-8">
          Loading earnings calendar...
        </div>
      ) : earnings.length === 0 ? (
        <div className="text-gray-400 text-sm text-center py-8">
          <div className="mb-2">📊</div>
          <div>No earnings data available</div>
        </div>
      ) : (
        <div className="space-y-6">
          {groupedEarnings.map(({ date, earnings: dayEarnings }) => (
            <div key={date} className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-white/10">
                <div 
                  className="text-sm font-semibold text-white/90 px-3 py-1 rounded-lg"
                  style={{
                    background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.2), rgba(59, 130, 246, 0.2))',
                    border: '1px solid rgba(255, 255, 255, 0.1)'
                  }}
                >
                  {formatDate(date)}
                </div>
                <div className="text-xs text-gray-400">
                  {dayEarnings.length} companies
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-xs text-gray-400 border-b border-white/5">
                      <th className="text-left py-2 px-3">Ticker</th>
                      <th className="text-left py-2 px-3">Company</th>
                      <th className="text-center py-2 px-3">Time</th>
                      <th className="text-left py-2 px-3">Quarter</th>
                      <th className="text-right py-2 px-3">Estimate</th>
                      <th className="text-right py-2 px-3">Actual</th>
                      <th className="text-right py-2 px-3">Surprise</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dayEarnings.map((earning, index) => (
                      <tr 
                        key={`${earning.ticker}-${index}`}
                        className="border-b border-white/5 hover:bg-white/5 transition-colors"
                      >
                        <td className="py-3 px-3">
                          <span className="text-white/90 font-semibold">
                            {earning.ticker}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-gray-300">
                          {earning.company_name}
                        </td>
                        <td className="py-3 px-3 text-center">
                          <span className={`text-xs font-semibold ${getTimeColor(earning.time)}`}>
                            {earning.time}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-gray-300">
                          {earning.quarter}
                        </td>
                        <td className="py-3 px-3 text-right text-gray-300">
                          ${earning.estimate}
                        </td>
                        <td className="py-3 px-3 text-right text-white/90">
                          {earning.actual ? `$${earning.actual}` : '—'}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <span className={`font-semibold ${getSurpriseColor(earning.surprise)}`}>
                            {earning.surprise 
                              ? `${getSurpriseIcon(earning.surprise)} $${Math.abs(earning.surprise)}`
                              : '—'
                            }
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EarningsCalendar;