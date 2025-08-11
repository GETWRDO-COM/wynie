import React, { useEffect, useMemo, useState } from 'react';
import WeatherWidget from './WeatherWidget';

// Utilities for time/date and market schedule
function parseInTZ(now, timeZone) {
  const fmt = new Intl.DateTimeFormat('en-GB', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).format(now);
  const [datePart, timePart] = fmt.split(', ');
  const [d, m, y] = datePart.split('/').map(s => parseInt(s, 10));
  const [hh, mm, ss] = timePart.split(':').map(s => parseInt(s, 10));
  return { y, m, d, hh, mm, ss };
}
function getWeekday(now, timeZone) { return new Intl.DateTimeFormat('en-US', { timeZone, weekday: 'short' }).format(now); }
function secondsUntil(now, timeZone, targetH, targetM) { const t = parseInTZ(now, timeZone); const nowSec = t.hh * 3600 + t.mm * 60 + t.ss; const targetSec = targetH * 3600 + targetM * 60; return targetSec - nowSec; }
function formatHMS(totalSec) { const s = Math.max(0, Math.floor(totalSec)); const h = Math.floor(s / 3600); const m = Math.floor((s % 3600) / 60); const sec = Math.floor(s % 60); return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`; }

// Holiday helpers
function easterSunday(year) { const a=year%19,b=Math.floor(year/100),c=year%100,d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,m=Math.floor((a+11*h+22*l)/451),month=Math.floor((h+l-7*m+114)/31),day=((h+l-7*m+114)%31)+1; return new Date(Date.UTC(year,month-1,day)); }
function observedDate(date) { const d=new Date(date.getTime()); const day=d.getUTCDay(); if(day===6) d.setUTCDate(d.getUTCDate()-1); if(day===0) d.setUTCDate(d.getUTCDate()+1); return d; }
function nthWeekdayOfMonthUTC(year, monthIndex, weekday, n){const d=new Date(Date.UTC(year,monthIndex,1));let c=0;while(d.getUTCMonth()===monthIndex){if(d.getUTCDay()===weekday){c+=1;if(c===n) return new Date(d.getTime());} d.setUTCDate(d.getUTCDate()+1);}return new Date(Date.UTC(year,monthIndex,1));}
function lastWeekdayOfMonthUTC(year, monthIndex, weekday){const d=new Date(Date.UTC(year,monthIndex+1,0));while(d.getUTCDay()!==weekday){d.setUTCDate(d.getUTCDate()-1);}return new Date(d.getTime());}
function isSameYMD(a,b){return a.getUTCFullYear()===b.getUTCFullYear()&&a.getUTCMonth()===b.getUTCMonth()&&a.getUTCDate()===b.getUTCDate();}
function nyseHolidays(year){ const list=[]; list.push({ name:"New Year's Day", date: observedDate(new Date(Date.UTC(year,0,1))) }); list.push({ name:'Martin Luther King Jr. Day', date: nthWeekdayOfMonthUTC(year,0,1,3)}); list.push({ name:"Presidents' Day", date: nthWeekdayOfMonthUTC(year,1,1,3)}); const easter=easterSunday(year); const gf=new Date(easter.getTime()); gf.setUTCDate(gf.getUTCDate()-2); list.push({ name:'Good Friday', date: gf }); list.push({ name:'Memorial Day', date: lastWeekdayOfMonthUTC(year,4,1)}); list.push({ name:'Juneteenth', date: observedDate(new Date(Date.UTC(year,5,19))) }); list.push({ name:'Independence Day', date: observedDate(new Date(Date.UTC(year,6,4))) }); list.push({ name:'Labor Day', date: nthWeekdayOfMonthUTC(year,8,1,1)}); list.push({ name:'Thanksgiving Day', date: nthWeekdayOfMonthUTC(year,10,4,4)}); list.push({ name:'Christmas Day', date: observedDate(new Date(Date.UTC(year,11,25))) }); return list; }
function nyseHolidayToday(nowET){ const parsed=parseInTZ(nowET,'America/New_York'); const todayUTC=new Date(Date.UTC(parsed.y,parsed.m-1,parsed.d)); const list=[...nyseHolidays(parsed.y), ...nyseHolidays(parsed.y-1), ...nyseHolidays(parsed.y+1)]; for(const h of list){ if(isSameYMD(h.date,todayUTC)) return h.name; } return null; }

function nextNYSEOpenClose(now){ const tz='America/New_York'; const wd=getWeekday(now,tz); const isWeekend = wd==='Sat'||wd==='Sun'; const toOpen=secondsUntil(now,tz,9,30); const toClose=secondsUntil(now,tz,16,0); const holidayName=nyseHolidayToday(now);
  if(!isWeekend && !holidayName && toOpen<=0 && toClose>0){ return { status:'Market Open', countdownLabel:'Closes in', seconds:toClose, holidayName:null, nextOpenText:null }; }
  if(!isWeekend && !holidayName && toOpen>0){ const nextOpenText=new Intl.DateTimeFormat('en-US',{ timeZone: tz, weekday:'short', month:'short', day:'2-digit', hour:'numeric', minute:'2-digit'}).format(new Date(now.getTime()+toOpen*1000)); return { status:'Market Closed', countdownLabel:'Opens in', seconds:toOpen, holidayName:null, nextOpenText }; }
  // find next business day open
  let days=1; while(true){ const candidate=new Date(now.getTime()); candidate.setUTCDate(candidate.getUTCDate()+days); const w=getWeekday(candidate,tz); const weekend = w==='Sat'||w==='Sun'; if(!weekend && !nyseHolidayToday(candidate)) break; days+=1; }
  const t=parseInTZ(now,tz); const secondsToMidnight=(24*3600)-(t.hh*3600+t.mm*60+t.ss); const secondsWholeDays=(days-1)*24*3600; const secondsNextDayToOpen=9*3600+30*60; const total=secondsToMidnight+secondsWholeDays+secondsNextDayToOpen; const nextOpenDate=new Date(now.getTime()+total*1000); const nextOpenText=new Intl.DateTimeFormat('en-US',{ timeZone: tz, weekday:'short', month:'short', day:'2-digit', hour:'numeric', minute:'2-digit'}).format(nextOpenDate); return { status:'Market Closed', countdownLabel:'Opens in', seconds: total, holidayName: holidayName || null, nextOpenText };
}

const HeroBanner = ({ user }) => {
  const [now, setNow] = useState(new Date());
  const [status, setStatus] = useState({ status: 'Calculating...', countdownLabel: '', seconds: 0, holidayName: null, nextOpenText: null });

  useEffect(() => { const timer=setInterval(()=>setNow(new Date()),1000); return () => clearInterval(timer); }, []);
  useEffect(() => { setStatus(nextNYSEOpenClose(now)); }, [now]);

  const saTime = new Intl.DateTimeFormat('en-GB', { timeZone: 'Africa/Johannesburg', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23' }).format(now);
  const todayLocal = new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'long', day: '2-digit' }).format(now);

  // Greeting in Afrikaans
  const hour = parseInTZ(now, 'Africa/Johannesburg').hh;
  const greet = hour < 12 ? 'Goeie môre' : hour < 18 ? 'Goeie middag' : 'Goeie naand';
  const name = user?.name || 'Alwyn';

  const openProgress = status.status === 'Market Open' ? Math.min(100, Math.max(0, (1 - status.seconds / (6.5 * 3600)) * 100)) : 0;

  return (
    <div className="glass-card p-6 relative overflow-hidden glow-ring">
      {/* Glow halos */}
      <div className="absolute -top-24 -left-24 w-[800px] h-[800px] rounded-full opacity-[0.12] blur-3xl" style={{ background: 'radial-gradient(circle, var(--brand-start), transparent 60%)' }} />
      <div className="absolute -bottom-24 -right-24 w-[800px] h-[800px] rounded-full opacity-[0.10] blur-3xl" style={{ background: 'radial-gradient(circle, var(--brand-end), transparent 60%)' }} />

      <div className="relative">
        <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-6">
          {/* Left: Title and greeting */}
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs text-white/90 border border-white/10" style={{ background: 'linear-gradient(135deg, color-mix(in_oklab, var(--brand-start) 12%, transparent), color-mix(in_oklab, var(--brand-end) 12%, transparent))' }}>
              <span>Premium Workspace</span>
            </div>
            <h1 className="mt-3 text-3xl md:text-4xl font-bold">HUNT BY WRDO</h1>
            <p className="text-gray-300 mt-1">{greet} {name}</p>
          </div>

          {/* Right: Tiles */}
          <div className="grid grid-cols-2 gap-4 w-full xl:w-auto">
            <div className="glass-panel p-4">
              <div className="text-xs text-gray-400">🇿🇦 Africa/Cape Town</div>
              <div className="text-xl font-bold">{saTime}</div>
            </div>
            <div className="glass-panel p-4">
              <div className="text-xs text-gray-400">🇺🇸 New York (ET)</div>
              <div className="text-xl font-bold">{new Intl.DateTimeFormat('en-US', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(now)}</div>
            </div>
            <div className="glass-panel p-4 col-span-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <div className="text-xs text-gray-400">Market Status</div>
                  <div className="text-white font-semibold">
                    {status.status}
                    {status.holidayName ? ` — ${status.holidayName}` : ''}
                  </div>
                  {status.nextOpenText && (
                    <div className="text-xs text-gray-400">Next open: {status.nextOpenText} ET</div>
                  )}
                </div>
                <div className="text-right">
                  <div className="text-xs text-gray-400">{status.countdownLabel}</div>
                  <div className="text-white font-mono text-lg">{formatHMS(status.seconds)}</div>
                </div>
              </div>
              <div className="mt-3 w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div className="h-2 rounded-full" style={{ width: `${openProgress}%`, background: 'linear-gradient(90deg, var(--brand-start), var(--brand-end))' }} />
              </div>
              <div className="mt-3">
                <WeatherWidget />
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 text-sm text-gray-400">Today: {todayLocal}</div>
      </div>
    </div>
  );
};

export default HeroBanner;