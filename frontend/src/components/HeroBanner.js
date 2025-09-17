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
  const [nextHoliday, setNextHoliday] = useState('');

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

  // Format current date and time in SA format
  const getCurrentDateTime = () => {
    const now = new Date();
    const options = { 
      weekday: 'long', 
      day: 'numeric', 
      month: 'long', 
      year: 'numeric' 
    };
    const dateStr = now.toLocaleDateString('en-ZA', options);
    const timeStr = now.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      hour12: true 
    });
    return `${dateStr} ${timeStr}`;
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
      setNextHoliday(getCurrentDateTime());
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
    <div className="glass-panel p-6">
      {/* Header Section with Bigger Title and Greeting */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="text-white font-extrabold text-5xl mb-3">
            <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
              HUNT by WRDO
            </span>
          </div>
          {/* Afrikaans Greeting with Gradient - Fixed Emoji */}
          <div className={`text-2xl font-bold bg-gradient-to-r ${greetingGradient} bg-clip-text text-transparent`}>
            {greeting}
          </div>
        </div>
        
        {/* Current Date and Time */}
        <div className="text-right">
          <div className="text-xs text-gray-400 mb-1">Today</div>
          <div className="text-lg text-white/90 font-semibold">{nextHoliday}</div>
        </div>
      </div>

      {/* Time Zones and Market Status - 3 Cards in Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* South Africa - Geolocation Based */}
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] backdrop-blur-md p-6 hover:from-white/10 hover:to-white/[0.05] transition-all duration-300">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-yellow-400 flex items-center justify-center text-sm font-bold">
              🇿🇦
            </div>
            <div>
              <div className="text-white font-semibold text-lg">South Africa</div>
              <div className="text-white/70 text-xs">SAST (UTC+2)</div>
            </div>
          </div>
          <div className={`text-3xl font-light bg-gradient-to-r ${timeGradients.sa} bg-clip-text text-transparent mb-2 tracking-wide`} style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace' }}>
            {saTime}
          </div>
          <div className="text-sm text-white/80 mb-3 font-medium">
            {new Date().toLocaleDateString('en-ZA', { timeZone: 'Africa/Johannesburg', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
          <div className="text-xs text-emerald-400 mb-2 font-medium">📍 Paarl, South Africa</div>
          <div className="text-xs text-orange-400 font-semibold">
            {getHolidayMessage('SA') || '🌟 No holidays today'}
          </div>
        </div>

        {/* New York, USA */}
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] backdrop-blur-md p-6 hover:from-white/10 hover:to-white/[0.05] transition-all duration-300">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-red-400 flex items-center justify-center text-sm font-bold">
              🇺🇸
            </div>
            <div>
              <div className="text-white font-semibold text-lg">New York, USA</div>
              <div className="text-white/70 text-xs">EDT (UTC-4)</div>
            </div>
          </div>
          <div className={`text-3xl font-light bg-gradient-to-r ${timeGradients.us} bg-clip-text text-transparent mb-2 tracking-wide`} style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace' }}>
            {usTime}
          </div>
          <div className="text-sm text-white/80 mb-3 font-medium">
            {new Date().toLocaleDateString('en-ZA', { timeZone: 'America/New_York', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
          <div className="text-xs text-cyan-400 mb-2 font-medium">📍 Eastern Time Zone</div>
          <div className="text-xs text-amber-400 font-semibold">
            {getHolidayMessage('US') || '📈 Normal trading hours'}
          </div>
        </div>

        {/* Market Status */}
        <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] backdrop-blur-md p-6 hover:from-white/10 hover:to-white/[0.05] transition-all duration-300">
          <div className="flex items-center justify-between mb-4">
            <div className="text-white/90 font-semibold text-lg">Market Status</div>
            <div className={`px-4 py-2 rounded-full text-sm font-bold ${
              status.status === 'Open' 
                ? 'text-green-300 bg-green-500/20 border border-green-400/40' 
                : 'text-red-300 bg-red-500/20 border border-red-400/40'
            }`}>
              ● {status.status.toUpperCase()}
            </div>
          </div>

          <div className="text-center mb-4">
            <div className="text-gray-400 text-sm mb-2 font-medium">{status.countdownLabel}:</div>
            <div className="text-3xl font-light text-cyan-300 mb-1 tracking-wide" style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace' }}>
              {formatHMS(status.seconds)}
            </div>
          </div>
          
          <div className="text-xs text-gray-400 text-center font-medium mb-2">
            NYSE/NASDAQ Regular Hours
          </div>
          <div className="text-xs text-blue-400 text-center font-semibold">
            🗓️ No market holidays today
          </div>
        </div>
      </div>

      {/* Weather Section - Moved Below */}
      <div className="mb-6">
        <WeatherWidget />
      </div>

      {/* Currency Exchange Section - Better Aligned */}
      <div className="mb-6">
        <CurrencyTicker />
      </div>
    </div>
  );
};

export default HeroBanner;