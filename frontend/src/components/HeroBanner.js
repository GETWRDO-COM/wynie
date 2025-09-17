import React, { useEffect, useMemo, useState } from 'react';
import WeatherWidget from './WeatherWidget';
import CurrencyTicker from './CurrencyTicker';

function pad(n){ return n.toString().padStart(2,'0'); }
function formatHMS(s){ if(s==null) return '--:--:--'; const h=Math.floor(s/3600), m=Math.floor((s%3600)/60), sec=s%60; return `${pad(h)}:${pad(m)}:${pad(sec)}`; }

const HeroBanner = ({ user }) => {
  const [saTime, setSaTime] = useState('');
  const [usTime, setUsTime] = useState('');
  const [status, setStatus] = useState({ status: 'Loading…', seconds: 0, countdownLabel: 'Opens in' });
  const [greeting, setGreeting] = useState('');
  const [greetingGradient, setGreetingGradient] = useState('');
  const [timeGradients, setTimeGradients] = useState({ sa: '', us: '' });
  const [currentDateTime, setCurrentDateTime] = useState('');
  const [reloading, setReloading] = useState(false);

  // Get username - should be Alwyn
  const userName = 'Alwyn';
  
  // User's birthday for special greetings
  const userBirthday = { month: 10, day: 13 }; // October 13, 1954

  // Time-based gradient generator
  const getTimeGradient = (hour) => {
    if (hour >= 5 && hour < 8) return 'from-orange-400 via-pink-400 to-purple-500'; // Sunrise
    if (hour >= 8 && hour < 17) return 'from-blue-400 via-cyan-400 to-blue-500'; // Daytime
    if (hour >= 17 && hour < 20) return 'from-orange-500 via-red-400 to-pink-500'; // Sunset
    return 'from-purple-900 via-blue-900 to-black'; // Night
  };

  // Enhanced Afrikaans greeting generator with special occasions and emojis
  const getAfrikaansGreeting = (hour) => {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();
    
    // Check for special occasions
    if (month === userBirthday.month && day === userBirthday.day) {
      return { text: `🎉 Gelukkige Verjaarsdag ${userName}!`, gradient: 'from-yellow-400 via-pink-400 to-purple-400' };
    }
    
    if (month === 12 && day === 25) {
      return { text: `🎄 Geseënde Kersfees ${userName}!`, gradient: 'from-red-400 via-green-400 to-gold' };
    }
    
    if (month === 12 && (day >= 24 && day <= 26)) {
      return { text: `🎄 Geseënde Kersfees ${userName}!`, gradient: 'from-red-400 via-green-400 to-gold' };
    }
    
    // Easter is complex to calculate, so we'll check approximate dates
    if (month === 3 || month === 4) {
      // Simple Easter check for common dates
      if ((month === 3 && day >= 25) || (month === 4 && day <= 25)) {
        const easterDates = [28, 29, 30, 31, 1, 2, 3, 4, 5]; // Common Easter range
        if (easterDates.includes(day)) {
          return { text: `🐰 Geseënde Paasfees ${userName}!`, gradient: 'from-yellow-400 via-pink-400 to-purple-400' };
        }
      }
    }
    
    // Regular time-based greetings with emojis
    if (hour >= 5 && hour < 12) return { text: `🌅 Goeie Môre ${userName}!`, gradient: 'from-yellow-400 via-orange-400 to-red-400' };
    if (hour >= 12 && hour < 17) return { text: `☀️ Goeie Middag ${userName}!`, gradient: 'from-blue-400 via-cyan-400 to-teal-400' };
    if (hour >= 17 && hour < 21) return { text: `🌆 Goeie Aand ${userName}!`, gradient: 'from-orange-400 via-pink-400 to-purple-400' };
    return { text: `🌙 Goeie Nag ${userName}!`, gradient: 'from-purple-400 via-blue-400 to-indigo-400' };
  };

  // Format current date and time in SA format - make it look better
  const getCurrentDateTime = () => {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-ZA', { 
      weekday: 'long', 
      day: 'numeric', 
      month: 'long', 
      year: 'numeric' 
    });
    const timeStr = now.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    });
    return { date: dateStr, time: timeStr };
  };

  // Get holiday messages
  const getHolidayMessage = (location = 'SA') => {
    const now = new Date();
    const heritageDay = new Date(2025, 8, 24); // September 24, 2025
    const columbusDay = new Date(2025, 9, 14); // October 14, 2025
    
    if (location === 'SA') {
      const diffTime = heritageDay - now;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        return '🎉 Today is Heritage Day!';
      } else if (diffDays > 0) {
        return `🎉 Heritage Day in ${diffDays} days`;
      }
    } else if (location === 'US') {
      const diffTime = columbusDay - now;
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        return '🇺🇸 Today is Columbus Day - Markets Closed';
      } else if (diffDays > 0 && diffDays <= 7) {
        return `🇺🇸 Columbus Day in ${diffDays} days - Affects Trading`;
      }
    }
    
    return null;
  };

  // Reload all data
  const reloadAllData = async () => {
    setReloading(true);
    // Trigger a page refresh or reload all components
    setTimeout(() => {
      window.location.reload();
    }, 500);
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      
      // SA Time and gradient
      const saHour = new Date(now.toLocaleString('en-US', { timeZone: 'Africa/Johannesburg' })).getHours();
      setSaTime(now.toLocaleTimeString('en-US', { timeZone: 'Africa/Johannesburg', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }));
      
      // US Time and gradient  
      const usHour = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' })).getHours();
      setUsTime(now.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }));
      
      // Set gradients based on time
      setTimeGradients({
        sa: getTimeGradient(saHour),
        us: getTimeGradient(usHour)
      });

      // Set greeting based on SA time
      const greetingData = getAfrikaansGreeting(saHour);
      setGreeting(greetingData.text);
      setGreetingGradient(greetingData.gradient);

      // Set current date and time
      setCurrentDateTime(getCurrentDateTime());
    }, 1000);
    return () => clearInterval(interval);
  }, [userName]);

  useEffect(() => {
    const computeMarket = () => {
      const now = new Date();
      const etNow = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
      const open = new Date(etNow); open.setHours(9, 30, 0, 0);
      const close = new Date(etNow); close.setHours(16, 0, 0, 0);
      let st = 'Closed'; let seconds = 0; let label = 'Opens in';
      if (etNow >= open && etNow <= close) { st = 'Open'; seconds = Math.max(0, Math.floor((close - etNow) / 1000)); label = 'Closes in'; }
      else if (etNow < open) { seconds = Math.max(0, Math.floor((open - etNow) / 1000)); }
      else { const tomorrow = new Date(etNow); tomorrow.setDate(tomorrow.getDate() + 1); tomorrow.setHours(9, 30, 0, 0); seconds = Math.max(0, Math.floor((tomorrow - etNow) / 1000)); }
      setStatus({ status: st, seconds, countdownLabel: label });
    };
    computeMarket();
    const id = setInterval(computeMarket, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="rounded-3xl border border-white/20 bg-black/40 backdrop-blur-2xl p-8 shadow-2xl hover:bg-black/50 transition-all duration-500 relative overflow-hidden">
      {/* Futuristic Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-purple-500/5 to-blue-500/5 rounded-3xl"></div>
      <div className="absolute inset-0 bg-gradient-to-tl from-white/[0.02] via-transparent to-white/[0.05] rounded-3xl"></div>
      
      {/* Main Header Section with Greeting and Better Date/Time */}
      <div className="relative z-10 flex items-center justify-between mb-8">
        <div className="flex-1">
          <div className="text-white font-extrabold text-6xl mb-4 drop-shadow-2xl">
            <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
              HUNT by WRDO
            </span>
          </div>
          {/* Afrikaans Greeting with Working Emojis */}
          <div className={`text-3xl font-bold bg-gradient-to-r ${greetingGradient} bg-clip-text text-transparent mb-4 drop-shadow-lg flex items-center gap-2`}>
            <span className="text-3xl">{greeting.split(' ')[0]}</span>
            <span>{greeting.split(' ').slice(1).join(' ')}</span>
          </div>
          {/* Today's Date and Time - Ultra Premium Dark Glass */}
          <div className="bg-black/60 backdrop-blur-xl rounded-2xl p-6 border border-white/20 shadow-xl">
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500/30 to-purple-500/30 backdrop-blur-xl border border-white/20 flex items-center justify-center shadow-lg">
                  <span className="text-2xl">📅</span>
                </div>
                <div>
                  <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider">Today's Date</div>
                  <div className="text-xl text-white font-bold drop-shadow-lg">{currentDateTime.date}</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-500/30 to-teal-500/30 backdrop-blur-xl border border-white/20 flex items-center justify-center shadow-lg">
                  <span className="text-2xl">🕐</span>
                </div>
                <div>
                  <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider">Current Time</div>
                  <div className="text-2xl text-cyan-400 font-mono font-bold drop-shadow-lg">{currentDateTime.time}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Line 1: Time Cards - Geolocation & Fixed Flags */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
        {/* South Africa - Geolocation Header with Working Flags */}
        <div className="rounded-2xl border border-white/20 bg-black/50 backdrop-blur-2xl p-6 hover:bg-black/60 transition-all duration-300 shadow-xl">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-green-500/40 to-yellow-500/40 backdrop-blur-xl border border-white/20 flex items-center justify-center shadow-lg">
              <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjMDA3QTNEIi8+CjxyZWN0IHdpZHRoPSIyNCIgaGVpZ2h0PSI0IiBmaWxsPSIjRkZCMzEzIi8+CjxyZWN0IHk9IjQiIHdpZHRoPSIyNCIgaGVpZ2h0PSI0IiBmaWxsPSIjRkZGRkZGIi8+CjxyZWN0IHk9IjgiIHdpZHRoPSIyNCIgaGVpZ2h0PSI4IiBmaWxsPSIjMDA3QTNEIi8+CjxyZWN0IHk9IjE2IiB3aWR0aD0iMjQiIGhlaWdodD0iNCIgZmlsbD0iI0ZGRkZGRiIvPgo8cmVjdCB5PSIyMCIgd2lkdGg9IjI0IiBoZWlnaHQ9IjQiIGZpbGw9IiNGRkIzMTMiLz4KPC9zdmc+" alt="SA Flag" className="w-6 h-4" />
            </div>
            <div>
              <div className="text-white font-bold text-xl drop-shadow-lg">Paarl, South Africa</div>
              <div className="text-white/70 text-sm font-medium">SAST (UTC+2)</div>
            </div>
          </div>
          <div className={`text-5xl font-light bg-gradient-to-r ${timeGradients.sa} bg-clip-text text-transparent mb-4 tracking-wide drop-shadow-2xl`} style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace', textShadow: '0 0 30px rgba(255,255,255,0.8)', filter: 'brightness(2) contrast(1.5)' }}>
            {saTime}
          </div>
          <div className="text-sm text-white/90 mb-4 font-semibold">
            {new Date().toLocaleDateString('en-ZA', { timeZone: 'Africa/Johannesburg', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
          <div className="text-sm text-orange-400 font-bold">
            {getHolidayMessage('SA') || '🌟 No holidays today'}
          </div>
        </div>

        {/* New York, USA - Enhanced Readability */}
        <div className="rounded-2xl border border-white/20 bg-black/50 backdrop-blur-2xl p-6 hover:bg-black/60 transition-all duration-300 shadow-xl">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500/40 to-red-500/40 backdrop-blur-xl border border-white/20 flex items-center justify-center shadow-lg">
              <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjMDAyODY4Ii8+CjxyZWN0IHdpZHRoPSIyNCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIi8+CjxyZWN0IHk9IjQiIHdpZHRoPSIyNCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkY0MDQwIi8+CjxyZWN0IHk9IjgiIHdpZHRoPSIyNCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkZGRkZGIi8+CjxyZWN0IHk9IjEyIiB3aWR0aD0iMjQiIGhlaWdodD0iMiIgZmlsbD0iI0ZGNDA0MCIvPgo8cmVjdCB5PSIxNiIgd2lkdGg9IjI0IiBoZWlnaHQ9IjIiIGZpbGw9IiNGRkZGRkYiLz4KPHJlY3QgeT0iMjAiIHdpZHRoPSIyNCIgaGVpZ2h0PSIyIiBmaWxsPSIjRkY0MDQwIi8+CjxyZWN0IHdpZHRoPSIxMCIgaGVpZ2h0PSIxMiIgZmlsbD0iIzAwMjg2OCIvPgo8L3N2Zz4=" alt="US Flag" className="w-6 h-4" />
            </div>
            <div>
              <div className="text-white font-bold text-xl drop-shadow-lg">New York, USA</div>
              <div className="text-white/70 text-sm font-medium">EDT (UTC-4)</div>
            </div>
          </div>
          <div className={`text-5xl font-light bg-gradient-to-r ${timeGradients.us} bg-clip-text text-transparent mb-4 tracking-wide drop-shadow-2xl`} style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace', textShadow: '0 0 30px rgba(255,255,255,1)', filter: 'brightness(2.5) contrast(1.8)' }}>
            {usTime}
          </div>
          <div className="text-sm text-white/90 mb-4 font-semibold">
            {new Date().toLocaleDateString('en-ZA', { timeZone: 'America/New_York', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
          <div className="text-sm text-amber-400 font-bold">
            {getHolidayMessage('US') || '📈 Normal trading hours'}
          </div>
        </div>

        {/* Market Status - Enhanced */}
        <div className="rounded-2xl border border-white/20 bg-black/50 backdrop-blur-2xl p-6 hover:bg-black/60 transition-all duration-300 shadow-xl">
          <div className="flex items-center justify-between mb-6">
            <div className="text-white/90 font-bold text-xl drop-shadow-lg">Market Status</div>
            <div className={`px-4 py-2 rounded-xl text-sm font-bold border-2 shadow-lg ${
              status.status === 'Open' 
                ? 'text-green-300 bg-green-500/30 border-green-400/60 shadow-green-500/20' 
                : 'text-red-300 bg-red-500/30 border-red-400/60 shadow-red-500/20'
            }`}>
              ● {status.status.toUpperCase()}
            </div>
          </div>

          <div className="text-center mb-6">
            <div className="text-gray-400 text-sm mb-2 font-semibold uppercase tracking-wider">{status.countdownLabel}:</div>
            <div className="text-5xl font-light text-cyan-300 mb-1 tracking-wide drop-shadow-2xl" style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace', textShadow: '0 0 30px rgba(6, 182, 212, 0.8)' }}>
              {formatHMS(status.seconds)}
            </div>
          </div>
          
          <div className="text-sm text-gray-400 text-center font-semibold mb-2 uppercase tracking-wider">
            NYSE/NASDAQ Regular Hours
          </div>
          <div className="text-sm text-blue-400 text-center font-bold">
            🗓️ No market holidays today
          </div>
        </div>
      </div>

      {/* Line 2: Weather and Currency Cards - Enhanced Dark Glass */}
      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Weather Section */}
        <div>
          <WeatherWidget />
        </div>

        {/* Currency Exchange Section */}
        <div>
          <CurrencyTicker />
        </div>
      </div>

      {/* Reload Button and Timestamp - Futuristic Bottom Right */}
      <div className="absolute bottom-6 right-8 flex items-center gap-4 z-20">
        <div className="text-xs text-gray-400 font-medium backdrop-blur-xl bg-black/40 px-3 py-2 rounded-lg border border-white/10">
          Last Update 1 min ago | {currentDateTime.date} | {currentDateTime.time}
        </div>
        <button 
          onClick={reloadAllData}
          disabled={reloading}
          className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-white text-sm font-bold rounded-xl transition-all hover:scale-110 disabled:opacity-50 shadow-xl border border-white/20"
        >
          {reloading ? '🔄' : '↻'} Reload
        </button>
      </div>
    </div>
  );
};

export default HeroBanner;