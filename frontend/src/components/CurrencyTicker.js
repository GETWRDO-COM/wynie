import React, { useEffect, useMemo, useState } from 'react';

function rel(ts){ if(!ts) return ''; const d=(ts instanceof Date? ts.getTime(): new Date(ts).getTime()); const diff=Math.round((d-Date.now())/60000); const rtf=new Intl.RelativeTimeFormat('en',{numeric:'auto'}); if(Math.abs(diff)<60) return rtf.format(diff,'minute'); const dh=Math.round(diff/60); if(Math.abs(dh)<24) return rtf.format(dh,'hour'); const dd=Math.round(dh/24); return rtf.format(dd,'day'); }

const CurrencyTicker = ({ compact = false }) => {
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

  const rows = useMemo(() =&gt; {
    if (!rates) return [];
    const inv = (x) =&gt; (x ? 1 / x : null);
    return [
      { flag: 'https://flagcdn.com/us.svg', code: 'USD', pair: '$1', zar: inv(rates.USD) },
      { flag: 'https://flagcdn.com/eu.svg', code: 'EUR', pair: '€1', zar: inv(rates.EUR) },
      { flag: 'https://flagcdn.com/gb.svg', code: 'GBP', pair: '£1', zar: inv(rates.GBP) },
      { flag: 'https://flagcdn.com/jp.svg', code: 'JPY', pair: '¥100', zar: rates.JPY ? (1 / rates.JPY) * 100 : null },
      { flag: 'https://flagcdn.com/cn.svg', code: 'CNY', pair: '¥1', zar: inv(rates.CNY) },
    ];
  }, [rates]);

  const updatedRel = rel(updatedAt);

  if (compact) {
    return (
      &lt;div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-xl p-3"&gt;
        &lt;div className="flex items-center justify-between mb-2"&gt;
          &lt;div className="text-white/90 font-semibold text-sm"&gt;Currency&lt;/div&gt;
          {err &amp;&amp; &lt;div className="text-[11px] text-red-400"&gt;{err}&lt;/div&gt;}
        &lt;/div&gt;
        {!rates ? (
          &lt;div className="text-gray-400 text-sm"&gt;Loading exchange rates...&lt;/div&gt;
        ) : (
          &lt;div className="grid grid-cols-5 gap-2"&gt;
            {rows.map((row) =&gt; (
              &lt;div key={row.code} className="text-center p-2 rounded-lg bg-black/40 border border-white/10"&gt;
                &lt;div className="flex items-center justify-center gap-1 mb-1"&gt;
                  &lt;img src={row.flag} alt={row.code} className="w-5 h-4 rounded-sm border border-white/10" /&gt;
                  &lt;span className="font-semibold text-white text-xs"&gt;{row.code}&lt;/span&gt;
                &lt;/div&gt;
                &lt;div className="text-[10px] text-gray-400 mb-1 uppercase"&gt;{row.pair}&lt;/div&gt;
                &lt;div className="text-white font-bold text-base"&gt;R{row.zar ? row.zar.toFixed(2) : '--'}&lt;/div&gt;
              &lt;/div&gt;
            ))}
          &lt;/div&gt;
        )}
      &lt;/div&gt;
    );
  }

  return (
    &lt;div className="rounded-2xl border border-white/20 bg-black/50 backdrop-blur-2xl p-6 hover:bg-black/60 transition-all duration-300 shadow-xl overflow-hidden relative"&gt;
      {/* Futuristic Background Gradient */}
      &lt;div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-pink-500/5 to-cyan-500/5 rounded-2xl"&gt;&lt;/div&gt;
      
      &lt;div className="relative z-10"&gt;
        &lt;div className="flex items-center justify-between mb-6"&gt;
          &lt;div className="text-white/90 font-bold text-xl drop-shadow-lg"&gt;Currency Exchange&lt;/div&gt;
          {err &amp;&amp; &lt;div className="text-sm text-red-400 font-semibold bg-red-500/20 px-3 py-1 rounded-lg border border-red-400/30"&gt;{err}&lt;/div&gt;}
        &lt;/div&gt;
        
        {!rates ? (
          &lt;div className="text-gray-400 text-sm font-semibold"&gt;Loading exchange rates...&lt;/div&gt;
        ) : (
          &lt;div className="grid grid-cols-2 lg:grid-cols-5 gap-4"&gt;
            {rows.map((row) =&gt; (
              &lt;div key={row.code} className="text-center p-4 rounded-xl bg-black/40 backdrop-blur-xl border border-white/20 hover:bg-black/60 transition-all duration-300 shadow-lg group"&gt;
                &lt;div className="flex items-center justify-center gap-3 mb-4"&gt;
                  &lt;img src={row.flag} alt={row.code} className="w-8 h-6 rounded-sm shadow-md border border-white/10" /&gt;
                  &lt;span className="font-bold text-white text-sm drop-shadow-lg"&gt;{row.code}&lt;/span&gt;
                &lt;/div&gt;
                &lt;div className="text-xs text-gray-400 mb-3 font-semibold uppercase tracking-wider"&gt;{row.pair}&lt;/div&gt;
                &lt;div className="text-white font-bold text-2xl drop-shadow-lg group-hover:text-cyan-400 transition-colors"&gt;
                  R{row.zar ? row.zar.toFixed(2) : '--'}
                &lt;/div&gt;
              &lt;/div&gt;
            ))}
          &lt;/div&gt;
        )}
      &lt;/div&gt;
    &lt;/div&gt;
  );
};

export default CurrencyTicker;