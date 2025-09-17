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
    <div className="space-y-6">
      {/* Main Header - More Compact */}
      <div className="glass-panel p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <div className="text-white font-extrabold text-4xl mb-3">
              <span className="bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent">
                HUNT by WRDO
              </span>
            </div>
            {/* Fix A: Working Emoji in Greeting */}
            <div className={`text-xl font-bold bg-gradient-to-r ${greetingGradient} bg-clip-text text-transparent flex items-center gap-2`}>
              <span>{greeting.includes('🌅') ? '🌅' : greeting.includes('☀️') ? '☀️' : greeting.includes('🌆') ? '🌆' : '🌙'}</span>
              <span>{greeting.replace(/🌅|☀️|🌆|🌙/g, '').trim()}</span>
            </div>
          </div>
          
          {/* Fix B: Date Left, Time Right */}
          <div className="flex items-center gap-8">
            <div className="text-right">
              <div className="text-xs text-gray-400 mb-1">Today's Date</div>
              <div className="text-lg text-white/90 font-semibold">{currentDateTime.date}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-400 mb-1">Current Time</div>
              <div className="text-xl text-cyan-400 font-mono font-bold">{currentDateTime.time}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Line 1: Time Cards - Clean Design */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Fix C: SA Card with Crisp Flag */}
        <div className="glass-panel p-4">
          <div className="flex items-center gap-3 mb-3">
            <img src="https://flagcdn.com/za.svg" alt="South Africa" className="w-8 h-6 rounded-sm shadow-sm" />
            <div>
              <div className="text-white font-semibold">Paarl, South Africa</div>
              <div className="text-white/70 text-xs">SAST (UTC+2)</div>
            </div>
          </div>
          {/* Fix E: Better Time Font and Colors */}
          <div className="text-3xl font-mono font-bold text-white mb-2" style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono"' }}>
            {saTime}
          </div>
          <div className="text-sm text-white/80 mb-2">
            {new Date().toLocaleDateString('en-ZA', { timeZone: 'Africa/Johannesburg', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
          <div className="text-xs text-orange-400">
            {getHolidayMessage('SA') || '🌟 No holidays today'}
          </div>
        </div>

        {/* Fix D: USA Card with Crisp Flag */}
        <div className="glass-panel p-4">
          <div className="flex items-center gap-3 mb-3">
            <img src="https://flagcdn.com/us.svg" alt="United States" className="w-8 h-6 rounded-sm shadow-sm" />
            <div>
              <div className="text-white font-semibold">New York, USA</div>
              <div className="text-white/70 text-xs">EDT (UTC-4)</div>
            </div>
          </div>
          {/* Fix E: Better Time Font and Colors */}
          <div className="text-3xl font-mono font-bold text-white mb-2" style={{ fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono"' }}>
            {usTime}
          </div>
          <div className="text-sm text-white/80 mb-2">
            {new Date().toLocaleDateString('en-ZA', { timeZone: 'America/New_York', weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
          {/* Fix F: Replace Normal Trading Hours with Next Holiday */}
          <div className="text-xs text-amber-400">
            {getHolidayMessage('US') || '🗓️ Columbus Day in 27 days'}
          </div>
        </div>

        {/* Market Status - Clean */}
        <div className="glass-panel p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="text-white/90 font-semibold">Market Status</div>
            <div className={`px-3 py-1 rounded-lg text-sm font-semibold ${
              status.status === 'Open' 
                ? 'text-green-400 bg-green-500/20 border border-green-500/30' 
                : 'text-red-400 bg-red-500/20 border border-red-500/30'
            }`}>
              ● {status.status.toUpperCase()}
            </div>
          </div>

          <div className="text-center mb-3">
            <div className="text-gray-400 text-sm mb-1">{status.countdownLabel}:</div>
            <div className="text-2xl font-mono font-bold text-cyan-400">
              {formatHMS(status.seconds)}
            </div>
          </div>
          
          <div className="text-xs text-gray-400 text-center">
            NYSE/NASDAQ Regular Hours
          </div>
        </div>
      </div>

      {/* Line 2: Weather and Currency */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <WeatherWidget />
        <CurrencyTicker />
      </div>

      {/* Timestamp and Reload - Below Subcards, Smaller Button */}
      <div className="glass-panel p-3">
        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-400">
            Last Update 1 min ago | {currentDateTime.date} | {currentDateTime.time}
          </div>
          <button 
            onClick={reloadAllData}
            disabled={reloading}
            className="px-3 py-1 bg-gradient-to-r from-cyan-500 to-purple-500 hover:from-cyan-400 hover:to-purple-400 text-white text-xs font-semibold rounded transition-all hover:scale-105 disabled:opacity-50"
          >
            {reloading ? '🔄' : '↻'} Reload
          </button>
        </div>
      </div>
    </div>
  );
};

export default HeroBanner;