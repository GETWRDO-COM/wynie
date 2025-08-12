import React, { useEffect, useState } from 'react';
import WeatherWidget from './WeatherWidget';
import CurrencyTicker from './CurrencyTicker';
import NewsSection from './NewsSection';

function parseInTZ(now, timeZone) {
  const fmt = new Intl.DateTimeFormat('en-GB', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(now);
  const [datePart, timePart] = fmt.split(', ');
  const [d, m, y] = datePart.split('/').map(s => parseInt(s, 10));
  const [hh, mm, ss] = timePart.split(':').map(s => parseInt(s, 10));
  return { y, m, d, hh, mm, ss };
}
function secondsUntil(now, timeZone, targetH, targetM) {
  const t = parseInTZ(now, timeZone);
  const nowSec = t.hh * 3600 + t.mm * 60 + t.ss;
  const targetSec = targetH * 3600 + targetM * 60;
  return targetSec - nowSec;
}
function formatHMS(totalSec) {
  const s = Math.max(0, Math.floor(totalSec));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}
function nextNYSEOpenClose(now) {
  const tz = 'America/New_York';
  const wd = new Intl.DateTimeFormat('en-US', { timeZone: tz, weekday:'short'}).format(now);
  const isWeekend = wd==='Sat'||wd==='Sun';
  const toOpen = secondsUntil(now, tz, 9, 30);
  const toClose = secondsUntil(now, tz, 16, 0);
  if (!isWeekend && toOpen <= 0 && toClose > 0) {
    return { status:'Market Open', countdownLabel:'Closes in', seconds:toClose };
  }
  if (!isWeekend && toOpen > 0) {
    return { status:'Market Closed', countdownLabel:'Opens in', seconds:toOpen };
  }
  // Weekend: show time to Monday 9:30
  const t = parseInTZ(now, tz);
  const secondsToMidnight = (24*3600) - (t.hh*3600+t.mm*60+t.ss);
  const daysAhead = (wd==='Sat') ? 2 : 1; // Sat -> Mon, Sun -> Mon
  const total = secondsToMidnight + (daysAhead-1)*24*3600 + (9*3600+30*60);
  return { status:'Market Closed', countdownLabel:'Opens in', seconds: total };
}

const HeroBanner = ({ user }) => {
  const [now, setNow] = useState(new Date());
  const [status, setStatus] = useState({ status: 'Calculating...', countdownLabel: '', seconds: 0 });

  useEffect(() => { const timer=setInterval(()=>setNow(new Date()),1000); return () => clearInterval(timer); }, []);
  useEffect(() => { setStatus(nextNYSEOpenClose(now)); }, [now]);

  const localTZ = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Africa/Johannesburg';
  const saTime = new Intl.DateTimeFormat('en-US', { timeZone: 'Africa/Johannesburg', hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true }).format(now).toUpperCase();
  const usTime = new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true }).format(now).toUpperCase();
  const todayLocal = new Intl.DateTimeFormat('en-GB', { weekday: 'long', year: 'numeric', month: 'long', day: '2-digit', timeZone: localTZ }).format(now);

  const hourLocal = parseInTZ(now, localTZ).hh;
  let greetIcon = '🌙'; if (hourLocal < 12) greetIcon = '☀️'; else if (hourLocal < 18) greetIcon = '🌤️';
  const greet = hourLocal < 12 ? 'Goeie môre' : hourLocal < 18 ? 'Goeie middag' : 'Goeie naand';
  const name = user?.name || 'Alwyn';

  return (
    <div className="relative">
      <div className="relative rounded-2xl border border-white/10 bg-black/40 backdrop-blur-2xl p-6 shadow-[0_20px_60px_-20px_rgba(0,0,0,0.6)]">
        <div className="pointer-events-none absolute -top-40 -left-40 w-[600px] h-[600px] rounded-full opacity-[0.12] blur-3xl" style={{ background: 'radial-gradient(circle, var(--brand-start), transparent 60%)' }} />
        <div className="pointer-events-none absolute -bottom-40 -right-40 w-[600px] h-[600px] rounded-full opacity-[0.10] blur-3xl" style={{ background: 'radial-gradient(circle, var(--brand-end), transparent 60%)' }} />

        {/* Brand at top */}
        <h1 className="mt-1 text-3xl md:text-4xl font-bold">HUNT by WRDO</h1>
        <p className="text-gray-300 mt-1 mb-4">{greet} {name} {greetIcon}</p>

        {/* Clocks + Market */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3 mb-4 items-stretch">
          <div className="glass-panel p-4">
            <div className="flex items-center gap-2 text-xs text-gray-400"><img src="https://flagcdn.com/za.svg" alt="ZA" className="w-4 h-3 rounded-sm" /><span>Africa/Cape Town</span></div>
            <div className="text-xl font-bold">{saTime}</div>
          </div>
          <div className="glass-panel p-4">
            <div className="flex items-center gap-2 text-xs text-gray-400"><img src="https://flagcdn.com/us.svg" alt="US" className="w-4 h-3 rounded-sm" /><span>USA (ET)</span></div>
            <div className="text-xl font-bold">{usTime}</div>
          </div>
          <div className="glass-panel p-4 flex items-center justify-between">
            <div>
              <div className="text-xs text-gray-400">Market Status</div>
              <div className="text-white font-semibold">{status.status}</div>
            </div>
            <div className="px-4 py-2 rounded-lg bg-white/10 border border-white/10 text-white font-bold text-base sm:text-lg">{status.countdownLabel} {formatHMS(status.seconds)}</div>
          </div>
        </div>

        {/* Date + Weather (same height cards) */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div className="glass-panel p-4 h-full flex items-center justify-between">
            <div className="text-white/90 font-semibold text-base sm:text-lg">{todayLocal}</div>
            <div className="text-xs text-gray-400">{Intl.DateTimeFormat().resolvedOptions().timeZone}</div>
          </div>
          <div className="h-full"><WeatherWidget /></div>
        </div>

        {/* FX + Top Headlines */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 items-start">
          <CurrencyTicker />
          <NewsSection api={{ get: async (url) => fetch((process.env.REACT_APP_BACKEND_URL||'')+url).then(r=>r.json()).then(data => ({ data })) }} />
        </div>
      </div>
    </div>
  );
};

export default HeroBanner;