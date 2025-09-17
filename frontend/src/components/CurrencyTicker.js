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
    <div className="rounded-xl border border-white/10 bg-neutral-800/50 backdrop-blur-sm p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="text-white/90 font-semibold">Currency Exchange</div>
        <div className="text-xs text-gray-400">
          {err ? err : updatedRel ? `Updated ${updatedRel}` : 'Loading...'}
        </div>
      </div>
      
      {!rates ? (
        <div className="text-gray-400 text-sm">Loading exchange rates...</div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
          {rows.map((row) => (
            <div key={row.code} className="text-center p-3 rounded-lg bg-black/20 border border-white/5">
              <div className="flex items-center justify-center gap-2 mb-2">
                <img src={row.flag} alt={row.code} className="w-6 h-4 rounded-sm" />
                <span className="font-semibold text-white text-sm">{row.code}</span>
              </div>
              <div className="text-xs text-gray-400 mb-1">{row.pair}</div>
              <div className="text-white font-bold">
                R{row.zar ? row.zar.toFixed(2) : '--'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CurrencyTicker;