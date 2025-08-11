import React, { useEffect, useState } from 'react';

function parseET(now) {
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'America/New_York',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
  }).format(now);
  // format like 11/08/2025, 14:05:06
  const [datePart, timePart] = fmt.split(', ');
  const [d, m, y] = datePart.split('/').map(s => parseInt(s, 10));
  const [hh, mm, ss] = timePart.split(':').map(s => parseInt(s, 10));
  return { y, m, d, hh, mm, ss };
}

function getETWeekday(now) {
  return new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', weekday: 'short' }).format(now);
}

function secondsUntil(targetH, targetM, now) {
  const et = parseET(now);
  const nowSec = et.hh * 3600 + et.mm * 60 + et.ss;
  const targetSec = targetH * 3600 + targetM * 60;
  return targetSec - nowSec;
}

function formatHMS(totalSec) {
  const s = Math.max(0, totalSec);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

function nextOpenClose(now) {
  // Simple NYSE schedule (Mon-Fri): open 09:30, close 16:00 ET (ignores holidays)
  const wd = getETWeekday(now); // Mon, Tue, ...
  const isWeekend = wd === 'Sat' || wd === 'Sun';
  const toOpen = secondsUntil(9, 30, now);
  const toClose = secondsUntil(16, 0, now);

  if (!isWeekend && toOpen <= 0 && toClose > 0) {
    return { status: 'Market Open', countdownLabel: 'Closes in', seconds: toClose };
  }
  // If before open on a weekday
  if (!isWeekend && toOpen > 0) {
    return { status: 'Market Closed', countdownLabel: 'Opens in', seconds: toOpen };
  }
  // After close or weekend: compute seconds until next weekday 09:30
  // Add days until next Mon-Fri
  let addDays = 1;
  if (wd === 'Fri') addDays = 3; // next Monday
  if (wd === 'Sat') addDays = 2; // next Monday
  // For other days after close -> next day
  // Compute seconds to midnight ET
  const et = parseET(now);
  const secondsToMidnight = (24 * 3600) - (et.hh * 3600 + et.mm * 60 + et.ss);
  const secondsNextDayToOpen = (9 * 3600 + 30 * 60);
  // If Sat: we already set addDays=2 -> midnight to next day repeated; approximate as below
  const total = secondsToMidnight + (addDays - 1) * 24 * 3600 + secondsNextDayToOpen;
  return { status: 'Market Closed', countdownLabel: 'Opens in', seconds: total };
}

const HeroBanner = () => {
  const [now, setNow] = useState(new Date());
  const [status, setStatus] = useState({ status: 'Calculating...', countdownLabel: '', seconds: 0 });

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => { setStatus(nextOpenClose(now)); }, [now]);

  const saTime = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Africa/Johannesburg',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
  }).format(now);

  const usTime = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour: 'numeric'
  }).format(now);

  const today = new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'long', day: '2-digit' }).format(now);

  return (
    <div className="glass-card p-6 relative overflow-hidden">
      <div className="absolute inset-0 opacity-[0.08] pointer-events-none" style={{ background: 'radial-gradient(800px 400px at 10% -20%, var(--brand-start), transparent), radial-gradient(700px 400px at 110% 120%, var(--brand-end), transparent)' }} />
      <div className="relative">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          {/* Left: Title */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs text-white/90 border border-white/10" style={{ background: 'linear-gradient(135deg, color-mix(in_oklab, var(--brand-start) 12%, transparent), color-mix(in_oklab, var(--brand-end) 12%, transparent))' }}>
              <span>Premium Workspace</span>
            </div>
            <h1 className="mt-3 text-3xl md:text-4xl font-bold">HUNT BY WRDO</h1>
            <p className="text-gray-300 mt-1">Your Personal Trading Command Center</p>
          </div>

          {/* Right: Clocks + Market Status */}
          <div className="grid grid-cols-2 gap-4 w-full lg:w-auto">
            <div className="glass-panel p-4">
              <div className="text-xs text-gray-400">🇿🇦 South Africa</div>
              <div className="text-xl font-bold">{saTime}</div>
            </div>
            <div className="glass-panel p-4">
              <div className="text-xs text-gray-400">🇺🇸 New York (ET)</div>
              <div className="text-xl font-bold">{usTime}</div>
            </div>
            <div className="glass-panel p-4 col-span-2">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-400">Market Status</div>
                  <div className="text-white font-semibold">{status.status}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400">{status.countdownLabel}</div>
                  <div className="text-white font-mono text-lg">{formatHMS(status.seconds)}</div>
                </div>
              </div>
              <div className="mt-3 w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div className="h-2 rounded-full" style={{ width: status.status === 'Market Open' ? `${Math.max(0, (1 - status.seconds / (6.5 * 3600)) * 100)}%` : '0%', background: 'linear-gradient(90deg, var(--brand-start), var(--brand-end))' }} />
              </div>
            </div>
          </div>
        </div>

        {/* Footer line with date */}
        <div className="mt-6 text-sm text-gray-400">Today: {today}</div>
      </div>
    </div>
  );
};

export default HeroBanner;