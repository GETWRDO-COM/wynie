import React, { useEffect, useMemo, useState } from 'react';

// Utilities for time/date and market schedule
function parseInTZ(now, timeZone) {
  const fmt = new Intl.DateTimeFormat('en-GB', {
    timeZone,
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
  }).format(now);
  const [datePart, timePart] = fmt.split(', ');
  const [d, m, y] = datePart.split('/').map(s => parseInt(s, 10));
  const [hh, mm, ss] = timePart.split(':').map(s => parseInt(s, 10));
  return { y, m, d, hh, mm, ss };
}

function getWeekday(now, timeZone) {
  return new Intl.DateTimeFormat('en-US', { timeZone, weekday: 'short' }).format(now);
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

// Easter calculation (Anonymous Gregorian algorithm) to compute Good Friday (2 days before Easter Sunday)
function easterSunday(year) {
  const a = year % 19;
  const b = Math.floor(year / 100);
  const c = year % 100;
  const d = Math.floor(b / 4);
  const e = b % 4;
  const f = Math.floor((b + 8) / 25);
  const g = Math.floor((b - f + 1) / 3);
  const h = (19 * a + b - d - g + 15) % 30;
  const i = Math.floor(c / 4);
  const k = c % 4;
  const l = (32 + 2 * e + 2 * i - h - k) % 7;
  const m = Math.floor((a + 11 * h + 22 * l) / 451);
  const month = Math.floor((h + l - 7 * m + 114) / 31); // 3=March, 4=April
  const day = ((h + l - 7 * m + 114) % 31) + 1;
  return new Date(Date.UTC(year, month - 1, day));
}

function observedDate(date) {
  // If holiday falls on weekend, observe on Friday (if Saturday) or Monday (if Sunday)
  const d = new Date(date.getTime());
  const day = d.getUTCDay(); // 0=Sun 6=Sat
  if (day === 6) d.setUTCDate(d.getUTCDate() - 1);
  if (day === 0) d.setUTCDate(d.getUTCDate() + 1);
  return d;
}

function isSameYMD(a, b) {
  return a.getUTCFullYear() === b.getUTCFullYear() && a.getUTCMonth() === b.getUTCMonth() && a.getUTCDate() === b.getUTCDate();
}

function isNYSEHoliday(dateET) {
  // dateET is a Date in real time but we only compare Y-M-D in ET; convert to UTC day matching ET midnight
  // We'll approximate by using the ET Y-M-D from Intl and comparing to holiday list built in UTC
  const tz = 'America/New_York';
  const parsed = parseInTZ(dateET, tz); // get Y-M-D in ET
  const y = parsed.y;
  const holidays = [];

  // New Year's Day (Jan 1 observed)
  holidays.push(observedDate(new Date(Date.UTC(y, 0, 1))));
  // Martin Luther King Jr. Day (third Monday in January)
  holidays.push(nthWeekdayOfMonthUTC(y, 0, 1, 3));
  // Presidents' Day (third Monday in February)
  holidays.push(nthWeekdayOfMonthUTC(y, 1, 1, 3));
  // Good Friday (2 days before Easter Sunday)
  const easter = easterSunday(y);
  const goodFriday = new Date(easter.getTime());
  goodFriday.setUTCDate(goodFriday.getUTCDate() - 2);
  holidays.push(goodFriday);
  // Memorial Day (last Monday in May)
  holidays.push(lastWeekdayOfMonthUTC(y, 4, 1));
  // Juneteenth (June 19 observed)
  holidays.push(observedDate(new Date(Date.UTC(y, 5, 19))));
  // Independence Day (July 4 observed)
  holidays.push(observedDate(new Date(Date.UTC(y, 6, 4))));
  // Labor Day (first Monday in September)
  holidays.push(nthWeekdayOfMonthUTC(y, 8, 1, 1));
  // Thanksgiving Day (fourth Thursday in November)
  holidays.push(nthWeekdayOfMonthUTC(y, 10, 4, 4));
  // Christmas Day (Dec 25 observed)
  holidays.push(observedDate(new Date(Date.UTC(y, 11, 25))));

  const etMid = new Date(Date.UTC(parsed.y, parsed.m - 1, parsed.d));
  return holidays.some(h => isSameYMD(h, etMid));
}

function nthWeekdayOfMonthUTC(year, monthIndex, weekday, n) {
  // weekday: 0=Sun..6=Sat
  const d = new Date(Date.UTC(year, monthIndex, 1));
  let count = 0;
  while (d.getUTCMonth() === monthIndex) {
    if (d.getUTCDay() === weekday) {
      count += 1;
      if (count === n) return new Date(d.getTime());
    }
    d.setUTCDate(d.getUTCDate() + 1);
  }
  return new Date(Date.UTC(year, monthIndex, 1));
}

function lastWeekdayOfMonthUTC(year, monthIndex, weekday) {
  const d = new Date(Date.UTC(year, monthIndex + 1, 0)); // last day of month
  while (d.getUTCDay() !== weekday) {
    d.setUTCDate(d.getUTCDate() - 1);
  }
  return new Date(d.getTime());
}

function nextNYSEOpenClose(now) {
  // Market hours: 09:30–16:00 ET, Mon–Fri, excluding holidays
  const tz = 'America/New_York';
  const wd = getWeekday(now, tz); // Mon...Sun
  const isWeekend = wd === 'Sat' || wd === 'Sun';
  const toOpen = secondsUntil(now, tz, 9, 30);
  const toClose = secondsUntil(now, tz, 16, 0);

  const holiday = isNYSEHoliday(now);

  if (!isWeekend && !holiday && toOpen <= 0 && toClose > 0) {
    return { status: 'Market Open', countdownLabel: 'Closes in', seconds: toClose };
  }
  if (!isWeekend && !holiday && toOpen > 0) {
    return { status: 'Market Closed', countdownLabel: 'Opens in', seconds: toOpen };
  }
  // After close or weekend/holiday: compute seconds until next valid open at 09:30
  let days = 1;
  // If Friday or holiday Friday -> next business day could be Mon or later; loop until next non-holiday weekday
  while (true) {
    const next = new Date(now.getTime());
    next.setUTCDate(next.getUTCDate() + days);
    const w = getWeekday(next, tz);
    const weekend = w === 'Sat' || w === 'Sun';
    if (!weekend && !isNYSEHoliday(next)) break;
    days += 1;
  }
  const t = parseInTZ(now, tz);
  const secondsToMidnight = (24 * 3600) - (t.hh * 3600 + t.mm * 60 + t.ss);
  const secondsWholeDays = (days - 1) * 24 * 3600;
  const secondsNextDayToOpen = 9 * 3600 + 30 * 60;
  return { status: 'Market Closed', countdownLabel: 'Opens in', seconds: secondsToMidnight + secondsWholeDays + secondsNextDayToOpen };
}

const CurrencyTicker = () => {
  const [rates, setRates] = useState(null);
  const [error, setError] = useState('');

  const fetchRates = async () => {
    try {
      setError('');
      const resp = await fetch('https://api.exchangerate.host/latest?base=ZAR&symbols=USD,EUR,GBP,JPY,CNY');
      const data = await resp.json();
      if (!data || !data.rates) throw new Error('No rates');
      setRates(data.rates);
    } catch (e) {
      setError('Failed to load FX rates');
    }
  };

  useEffect(() => {
    fetchRates();
    const id = setInterval(fetchRates, 60_000);
    return () => clearInterval(id);
  }, []);

  const items = useMemo(() => {
    if (!rates) return [];
    // rates are quoted as 1 ZAR = X USD/EUR/...
    // We want 1 unit foreign = ? ZAR, so invert
    const inv = (x) => (x ? 1 / x : null);
    const usd = inv(rates.USD);
    const eur = inv(rates.EUR);
    const gbp = inv(rates.GBP);
    const jpy = inv(rates.JPY); // per 1 JPY
    const cny = inv(rates.CNY);
    return [
      { code: 'USD', flag: '🇺🇸', label: '$1', value: usd },
      { code: 'EUR', flag: '🇪🇺', label: '€1', value: eur },
      { code: 'GBP', flag: '🇬🇧', label: '£1', value: gbp },
      { code: 'JPY', flag: '🇯🇵', label: '¥100', value: jpy != null ? jpy * 100 : null },
      { code: 'CNY', flag: '🇨🇳', label: '¥1', value: cny },
    ];
  }, [rates]);

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      {items.map((it) => (
        <div key={it.code} className="px-2 py-1 rounded-lg text-xs text-white/90 border border-white/10" style={{ background: 'linear-gradient(135deg, color-mix(in_oklab, var(--brand-start) 10%, transparent), color-mix(in_oklab, var(--brand-end) 10%, transparent))' }}>
          <span className="mr-1">{it.flag}</span>
          <span className="mr-1">{it.label}</span>
          <span>= R{it.value != null ? it.value.toFixed(2) : '--'}</span>
        </div>
      ))}
      {error && <div className="text-xs text-red-300 ml-2">{error}</div>}
    </div>
  );
};

const HeroBanner = () => {
  const [now, setNow] = useState(new Date());
  const [status, setStatus] = useState({ status: 'Calculating...', countdownLabel: '', seconds: 0 });

  const browserTZ = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Africa/Johannesburg';
  const capeTownTZ = 'Africa/Johannesburg'; // Use Johannesburg timezone, label as Cape Town

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => { setStatus(nextNYSEOpenClose(now)); }, [now]);

  const saTime = new Intl.DateTimeFormat('en-GB', {
    timeZone: capeTownTZ,
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
  }).format(now);

  const usTime = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  }).format(now);

  const localTime = new Intl.DateTimeFormat('en-GB', {
    timeZone: browserTZ,
    hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'
  }).format(now);

  const todayLocal = new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'long', day: '2-digit', timeZone: browserTZ }).format(now);

  // Glow halo widths for open progress
  const openProgress = status.status === 'Market Open' ? Math.min(100, Math.max(0, (1 - status.seconds / (6.5 * 3600)) * 100)) : 0;

  return (
    <div className="glass-card p-6 relative overflow-hidden glow-ring">
      {/* Glow layers */}
      <div className="absolute -top-24 -left-24 w-[800px] h-[800px] rounded-full opacity-[0.12] blur-3xl" style={{ background: 'radial-gradient(circle, var(--brand-start), transparent 60%)' }} />
      <div className="absolute -bottom-24 -right-24 w-[800px] h-[800px] rounded-full opacity-[0.10] blur-3xl" style={{ background: 'radial-gradient(circle, var(--brand-end), transparent 60%)' }} />

      <div className="relative">
        <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-6">
          {/* Left: Title */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs text-white/90 border border-white/10" style={{ background: 'linear-gradient(135deg, color-mix(in_oklab, var(--brand-start) 12%, transparent), color-mix(in_oklab, var(--brand-end) 12%, transparent))' }}>
              <span>Premium Workspace</span>
            </div>
            <h1 className="mt-3 text-3xl md:text-4xl font-bold">HUNT BY WRDO</h1>
            <p className="text-gray-300 mt-1">Your Personal Trading Command Center</p>
          </div>

          {/* Right: Clocks + Market Status */}
          <div className="grid grid-cols-2 gap-4 w-full xl:w-auto">
            <div className="glass-panel p-4">
              <div className="text-xs text-gray-400">🇿🇦 Africa/Cape Town</div>
              <div className="text-xl font-bold">{saTime}</div>
            </div>
            <div className="glass-panel p-4">
              <div className="text-xs text-gray-400">🕒 Local ({browserTZ})</div>
              <div className="text-xl font-bold">{localTime}</div>
            </div>
            <div className="glass-panel p-4 col-span-2">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs text-gray-400">🇺🇸 New York (ET) — Market Status</div>
                  <div className="text-white font-semibold">{status.status}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400">{status.countdownLabel}</div>
                  <div className="text-white font-mono text-lg">{formatHMS(status.seconds)}</div>
                </div>
              </div>
              <div className="mt-3 w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div className="h-2 rounded-full" style={{ width: `${openProgress}%`, background: 'linear-gradient(90deg, var(--brand-start), var(--brand-end))' }} />
              </div>
              <CurrencyTicker />
            </div>
          </div>
        </div>

        {/* Footer line with date */}
        <div className="mt-6 text-sm text-gray-400">Today (Local): {todayLocal}</div>
      </div>
    </div>
  );
};

export default HeroBanner;