import React, { useEffect, useMemo, useState } from 'react';
import WeatherWidget from './WeatherWidget';

function pad(n){ return n.toString().padStart(2,'0'); }
function formatHMS(s){ if(s==null) return '--:--:--'; const h=Math.floor(s/3600), m=Math.floor((s%3600)/60), sec=s%60; return `${pad(h)}:${pad(m)}:${pad(sec)}`; }

const HeroBanner = ({ user }) => {
  const [saTime, setSaTime] = useState('');
  const [usTime, setUsTime] = useState('');
  const [status, setStatus] = useState({ status: 'Loading…', seconds: 0, countdownLabel: 'Opens in' });

  const todayLocal = useMemo(() => new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }), []);

  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      setSaTime(now.toLocaleTimeString('en-ZA', { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      const us = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(now);
      setUsTime(us);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

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
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-xs text-gray-400">Welcome back</div>
          <div className="text-white font-extrabold text-2xl">HUNT by WRDO</div>
        </div>
        <div className="text-white/80 text-sm">{todayLocal}</div>
      </div>

      {/* Clocks + Market */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-4 items-stretch">
        <div className="glass-panel p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs text-gray-400"><img src="https://flagcdn.com/za.svg" alt="ZA" className="w-4 h-3 rounded-sm" /><span>South Africa</span></div>
              <div className="text-xl font-bold">{saTime}</div>
            </div>
            <div>
              <div className="flex items-center gap-2 text-xs text-gray-400"><img src="https://flagcdn.com/us.svg" alt="US" className="w-4 h-3 rounded-sm" /><span>USA (ET)</span></div>
              <div className="text-xl font-bold">{usTime}</div>
            </div>
          </div>
        </div>
        <div className="glass-panel p-4 flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-400">Market Status</div>
            <div className={`${String(status.status).toLowerCase().includes('open') ? 'text-green-400' : 'text-red-400'} font-semibold`}>{status.status}</div>
          </div>
          <div className={`px-4 py-2 rounded-lg border text-white font-bold text-base sm:text-lg ${String(status.status).toLowerCase().includes('open') ? 'bg-green-500/20 border-green-500/40 text-green-300' : 'bg-red-500/20 border-red-500/40 text-red-300'}`}>{status.countdownLabel} {formatHMS(status.seconds)}</div>
        </div>
      </div>

      {/* Date + Weather (same height cards) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        <div className="glass-panel p-4 h-full flex items-center justify-between">
          <div className="text-white/90 font-semibold text-base sm:text-lg">{todayLocal}</div>
          {/* remove explicit timezone text */}
        </div>
        <div className="h-full"><WeatherWidget /></div>
      </div>
    </div>
  );
};

export default HeroBanner;