import React, { useState, useEffect } from 'react';

const GlobalClock = () => {
  const [time, setTime] = useState(new Date());
  const [marketStatus, setMarketStatus] = useState('closed');
  const [gradients, setGradients] = useState({ sa: '', us: '' });

  // Time-based gradient generator
  const getTimeGradient = (hour) => {
    if (hour >= 5 && hour < 8) return 'from-orange-400 via-pink-400 to-purple-500'; // Sunrise
    if (hour >= 8 && hour < 17) return 'from-blue-400 via-cyan-400 to-blue-500'; // Daytime
    if (hour >= 17 && hour < 20) return 'from-orange-500 via-red-400 to-pink-500'; // Sunset
    return 'from-purple-900 via-blue-900 to-black'; // Night
  };

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      setTime(now);
      
      // Get hours for both timezones
      const saHour = new Date(now.toLocaleString('en-US', { timeZone: 'Africa/Johannesburg' })).getHours();
      const usHour = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' })).getHours();
      
      // Set gradients
      setGradients({
        sa: getTimeGradient(saHour),
        us: getTimeGradient(usHour)
      });
      
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
      hour12: true
    });
  };

  const saTime = formatTime(time, 'Africa/Johannesburg');
  const nyTime = formatTime(time, 'America/New_York');

  return (
    <div 
      className={`fixed bottom-4 right-4 z-40 rounded-xl border border-white/10 bg-gradient-to-br ${gradients.sa} bg-opacity-20 backdrop-blur-xl p-4 min-w-[200px]`}
      style={{ zIndex: 1000 }}
    >
      <div className="text-xs text-white/70 mb-2 text-center">Market Status</div>
      <div className={`text-xs font-semibold text-center mb-3 px-2 py-1 rounded ${
        marketStatus === 'open' 
          ? 'bg-green-500/30 text-green-300 border border-green-400/40' 
          : 'bg-red-500/30 text-red-300 border border-red-400/40'
      }`}>
        {marketStatus === 'open' ? '● MARKET OPEN' : '● MARKET CLOSED'}
      </div>
      
      <div className="space-y-3 text-sm">
        <div className={`rounded-lg border border-white/10 bg-gradient-to-r ${gradients.sa} bg-opacity-20 p-2`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">🇿🇦</span>
              <span className="text-white/90 font-semibold">SA</span>
            </div>
            <div className="text-white font-mono font-bold">{saTime}</div>
          </div>
        </div>
        
        <div className={`rounded-lg border border-white/10 bg-gradient-to-r ${gradients.us} bg-opacity-20 p-2`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg">🇺🇸</span>
              <span className="text-white/90 font-semibold">NY</span>
            </div>
            <div className="text-white font-mono font-bold">{nyTime}</div>
          </div>
        </div>
      </div>
    </div>
  );
};
export default GlobalClock;