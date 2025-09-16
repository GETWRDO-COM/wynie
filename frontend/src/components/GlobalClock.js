import React, { useState, useEffect } from 'react';

const GlobalClock = () => {
  const [time, setTime] = useState(new Date());
  const [marketStatus, setMarketStatus] = useState('closed');

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTime(now);
      
      // Calculate market status (NYSE hours: 9:30 AM - 4:00 PM ET)
      const nyTime = new Date(now.toLocaleString("en-US", {timeZone: "America/New_York"}));
      const hour = nyTime.getHours();
      const minute = nyTime.getMinutes();
      const dayOfWeek = nyTime.getDay(); // 0 = Sunday, 6 = Saturday
      
      // Check if it's a weekday and within market hours
      if (dayOfWeek >= 1 && dayOfWeek <= 5) {
        const currentMinutes = hour * 60 + minute;
        const marketOpen = 9 * 60 + 30; // 9:30 AM
        const marketClose = 16 * 60; // 4:00 PM
        
        if (currentMinutes >= marketOpen && currentMinutes < marketClose) {
          setMarketStatus('open');
        } else {
          setMarketStatus('closed');
        }
      } else {
        setMarketStatus('closed');
      }
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const formatTime = (date, timezone) => {
    return date.toLocaleString('en-US', {
      timeZone: timezone,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  const saTime = formatTime(time, 'Africa/Johannesburg');
  const nyTime = formatTime(time, 'America/New_York');

  return (
    <div 
      className="fixed bottom-4 right-4 z-40 glass-panel p-3 min-w-[200px]"
      style={{ zIndex: 1000 }}
    >
      <div className="text-xs text-gray-300 mb-2 text-center">Market Status</div>
      <div className={`text-xs font-semibold text-center mb-3 px-2 py-1 rounded ${
        marketStatus === 'open' 
          ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
          : 'bg-red-500/20 text-red-400 border border-red-500/30'
      }`}>
        {marketStatus === 'open' ? '● MARKET OPEN' : '● MARKET CLOSED'}
      </div>
      
      <div className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">🇿🇦</span>
            <span className="text-gray-300">SA</span>
          </div>
          <div className="text-white font-mono font-semibold">{saTime}</div>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-lg">🇺🇸</span>
            <span className="text-gray-300">NY</span>
          </div>
          <div className="text-white font-mono font-semibold">{nyTime}</div>
        </div>
      </div>
    </div>
  );
};

export default GlobalClock;