import React, { useEffect, useMemo, useState } from 'react';

function rel(ts){ if(!ts) return ''; const d=(ts instanceof Date? ts.getTime(): new Date(ts).getTime()); const diff=Math.round((d-Date.now())/60000); const rtf=new Intl.RelativeTimeFormat('en',{numeric:'auto'}); if(Math.abs(diff)<60) return rtf.format(diff,'minute'); const dh=Math.round(diff/60); if(Math.abs(dh)<24) return rtf.format(dh,'hour'); const dd=Math.round(dh/24); return rtf.format(dd,'day'); }

const CurrencyTicker = () => {
  const [rates, setRates] = useState(null);
  const [err, setErr] = useState('');
  const [updatedAt, setUpdatedAt] = useState(null);

  const fetchPrimary = async () => {
    const resp = await fetch('https://api.exchangerate.host/latest?base=ZAR&symbols=USD,EUR,GBP,JPY,CNY');
    const data = await resp.json();
    if (!data || !data.rates) throw new Error('no primary');
    return { rates: data.rates };
  };
  const fetchFallback = async () => {
    const resp = await fetch('https://open.er-api.com/v6/latest/ZAR');
    const data = await resp.json();
    if (data && data.result === 'success' && data.rates) return { rates: { USD: data.rates.USD, EUR: data.rates.EUR, GBP: data.rates.GBP, JPY: data.rates.JPY, CNY: data.rates.CNY } };
    throw new Error('no fallback');
  };

  const fetchRates = async () => {
    try {
      setErr('');
      try { const r = await fetchPrimary(); setRates(r.rates); setUpdatedAt(new Date()); }
      catch { const r = await fetchFallback(); setRates(r.rates); setUpdatedAt(new Date()); }
    } catch {
      setErr('FX unavailable');
    }
  };

  useEffect(() => { fetchRates(); const id = setInterval(fetchRates, 900000); return () => clearInterval(id); }, []);

  const rows = useMemo(() => {
    if (!rates) return [];
    const inv = (x) => (x ? 1 / x : null);
    return [
      { flag: 'https://flagcdn.com/us.svg', code: 'USD', pair: '$1', zar: inv(rates.USD) },
      { flag: 'https://flagcdn.com/eu.svg', code: 'EUR', pair: '€1', zar: inv(rates.EUR) },
      { flag: 'https://flagcdn.com/gb.svg', code: 'GBP', pair: '£1', zar: inv(rates.GBP) },
      { flag: 'https://flagcdn.com/jp.svg', code: 'JPY', pair: '¥100', zar: rates.JPY ? (1 / rates.JPY) * 100 : null },
      { flag: 'https://flagcdn.com/cn.svg', code: 'CNY', pair: '¥1', zar: inv(rates.CNY) },
    ];
  }, [rates]);

  const updatedRel = rel(updatedAt);

  return (
    <div className="rounded-2xl border border-white/20 bg-black/50 backdrop-blur-2xl p-6 hover:bg-black/60 transition-all duration-300 shadow-xl overflow-hidden relative">
      {/* Futuristic Background Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-pink-500/5 to-cyan-500/5 rounded-2xl"></div>
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div className="text-white/90 font-bold text-xl drop-shadow-lg">Currency Exchange</div>
          {err && <div className="text-sm text-red-400 font-semibold bg-red-500/20 px-3 py-1 rounded-lg border border-red-400/30">{err}</div>}
        </div>
        
        {!rates ? (
          <div className="text-gray-400 text-sm font-semibold">Loading exchange rates...</div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            {rows.map((row) => (
              <div key={row.code} className="text-center p-4 rounded-xl bg-black/40 backdrop-blur-xl border border-white/20 hover:bg-black/60 transition-all duration-300 shadow-lg group">
                <div className="flex items-center justify-center gap-3 mb-4">
                  <img src={row.flag} alt={row.code} className="w-8 h-6 rounded-sm shadow-md border border-white/10" />
                  <span className="font-bold text-white text-sm drop-shadow-lg">{row.code}</span>
                </div>
                <div className="text-xs text-gray-400 mb-3 font-semibold uppercase tracking-wider">{row.pair}</div>
                <div className="text-white font-bold text-2xl drop-shadow-lg group-hover:text-cyan-400 transition-colors">
                  R{row.zar ? row.zar.toFixed(2) : '--'}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CurrencyTicker;