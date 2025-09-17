import React, { useEffect, useState } from 'react';
import WeatherWidget from './WeatherWidget';
import CurrencyTicker from './CurrencyTicker';

function pad(n){ return n.toString().padStart(2,'0'); }
function formatHMS(s){ if(s==null) return '--:--:--'; const h=Math.floor(s/3600), m=Math.floor((s%3600)/60), sec=s%60; return `${pad(h)}:${pad(m)}:${pad(sec)}`; }

const HeroBanner = ({ user }) => {
  const [saTime, setSaTime] = useState('');
  const [usTime, setUsTime] = useState('');
  const [status, setStatus] = useState({ status: 'Loading…', seconds: 0, countdownLabel: 'Opens in' });
  const [greeting, setGreeting] = useState('');
  const [currentDate, setCurrentDate] = useState('');
  const [updatedAt, setUpdatedAt] = useState('');
  const [reloading, setReloading] = useState(false);

  const userName = 'Alwyn';

  // Greeting in Afrikaans with emoji kept subtle
  const getAfrikaansGreeting = (hour) => {
    if (hour >= 5 && hour < 12) return `🌅 Goeie Môre ${userName}!`;
    if (hour >= 12 && hour < 17) return `☀️ Goeie Middag ${userName}!`;
    if (hour >= 17 && hour < 21) return `🌆 Goeie Aand ${userName}!`;
    return `🌙 Goeie Nag ${userName}!`;
  };

  const formatDateSA = () => new Date().toLocaleDateString('en-ZA', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });

  // Simple market compute
  useEffect(() => {
    const compute = () => {
      const now = new Date();
      const saT = now.toLocaleTimeString('en-US', { timeZone: 'Africa/Johannesburg', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
      const usT = now.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
      setSaTime(saT);
      setUsTime(usT);

      const saHour = new Date(now.toLocaleString('en-US', { timeZone: 'Africa/Johannesburg' })).getHours();
      setGreeting(getAfrikaansGreeting(saHour));
      setCurrentDate(formatDateSA());

      const etNow = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }));
      const open = new Date(etNow); open.setHours(9,30,0,0);
      const close = new Date(etNow); close.setHours(16,0,0,0);
      let st = 'Closed'; let seconds = 0; let label = 'Opens in';
      if (etNow >= open && etNow <= close) { st = 'Open'; seconds = Math.max(0, Math.floor((close - etNow)/1000)); label = 'Closes in'; }
      else if (etNow < open) { seconds = Math.max(0, Math.floor((open - etNow)/1000)); }
      else { const tmr = new Date(etNow); tmr.setDate(tmr.getDate()+1); tmr.setHours(9,30,0,0); seconds = Math.max(0, Math.floor((tmr - etNow)/1000)); }
      setStatus({ status: st, seconds, countdownLabel: label });
      setUpdatedAt(new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true }));
    };
    compute();
    const id = setInterval(compute, 1000);
    return () => clearInterval(id);
  }, []);

  const reloadAllData = () => {
    setReloading(true);
    setTimeout(() => window.location.reload(), 400);
  };

  return (
    // MAIN CARD WRAPPER
    <div className="glass-panel p-5 lg:p-6 space-y-4">
      {/* Header: Greeting + Today's Date only (no current time) */}
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <div className="text-xl sm:text-2xl font-bold text-white/90 truncate">{greeting}</div>
          <div className="text-sm text-gray-400 mt-1">{currentDate}</div>
        </div>
      </div>

      {/* Row: SA, USA, Market Status - aligned times on one line */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        {/* SA Card */}
        <div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-xl p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <img src="https://flagcdn.com/za.svg" alt="South Africa" className="w-7 h-5 rounded-sm border border-white/10" />
              <div className="text-white/90 text-sm font-semibold">Paarl, South Africa</div>
            </div>
            <div className="text-2xl font-mono tracking-tight text-white" style={{fontFamily:'ui-monospace, SFMono-Regular, "SF Mono"'}}>{saTime}</div>
          </div>
        </div>

        {/* USA Card */}
        <div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-xl p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <img src="https://flagcdn.com/us.svg" alt="United States" className="w-7 h-5 rounded-sm border border-white/10" />
              <div className="text-white/90 text-sm font-semibold">New York, USA</div>
            </div>
            <div className="text-2xl font-mono tracking-tight text-white" style={{fontFamily:'ui-monospace, SFMono-Regular, "SF Mono"'}}>{usTime}</div>
          </div>
        </div>

        {/* Market Status */}
        <div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-xl p-3">
          <div className="flex items-center justify-between">
            <div className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border ${status.status === 'Open' ? 'text-green-400 bg-green-500/15 border-green-500/30' : 'text-red-400 bg-red-500/15 border-red-500/30'}`}>
              ● {status.status.toUpperCase()}
            </div>
            <div className="text-2xl font-mono tracking-tight text-cyan-400" style={{fontFamily:'ui-monospace, SFMono-Regular, "SF Mono"'}}>{formatHMS(status.seconds)}</div>
          </div>
          <div className="text-[11px] text-gray-400 mt-1 text-right">{status.countdownLabel}</div>
        </div>
      </div>

      {/* Row: Weather (compact) and Currency (compact) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <WeatherWidget compact />
        <CurrencyTicker compact />
      </div>

      {/* Footer: timestamp + reload at bottom-right */}
      <div className="flex items-center justify-between pt-2">
        <div className="text-xs text-gray-500">Updated {updatedAt}</div>
        <button onClick={reloadAllData} disabled={reloading} className="px-3 py-1.5 text-xs rounded-lg bg-white/5 border border-white/10 text-white hover:bg-white/10 disabled:opacity-50">
          {reloading ? 'Refreshing…' : 'Reload'}
        </button>
      </div>
    </div>
  );
};

export default HeroBanner;