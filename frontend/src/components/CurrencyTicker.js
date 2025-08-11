import React, { useEffect, useMemo, useState } from 'react';

const CurrencyTicker = () => {
  const [rates, setRates] = useState(null);
  const [err, setErr] = useState('');

  const fetchPrimary = async () => {
    const resp = await fetch('https://api.exchangerate.host/latest?base=ZAR&symbols=USD,EUR,GBP,JPY,CNY');
    const data = await resp.json();
    if (!data || !data.rates) throw new Error('no primary');
    return data.rates;
  };
  const fetchFallback = async () => {
    const resp = await fetch('https://open.er-api.com/v6/latest/ZAR');
    const data = await resp.json();
    if (data && data.result === 'success' && data.rates) return { USD: data.rates.USD, EUR: data.rates.EUR, GBP: data.rates.GBP, JPY: data.rates.JPY, CNY: data.rates.CNY };
    throw new Error('no fallback');
  };

  const fetchRates = async () => {
    try {
      setErr('');
      try { setRates(await fetchPrimary()); }
      catch { setRates(await fetchFallback()); }
    } catch {
      setErr('FX unavailable');
    }
  };

  useEffect(() => { fetchRates(); const id = setInterval(fetchRates, 60_000); return () => clearInterval(id); }, []);

  const rows = useMemo(() => {
    if (!rates) return [];
    const inv = (x) => (x ? 1 / x : null);
    return [
      { flag: 'https://flagcdn.com/us.svg', pair: '$1', zar: inv(rates.USD) },
      { flag: 'https://flagcdn.com/eu.svg', pair: '€1', zar: inv(rates.EUR) },
      { flag: 'https://flagcdn.com/gb.svg', pair: '£1', zar: inv(rates.GBP) },
      { flag: 'https://flagcdn.com/jp.svg', pair: '¥100', zar: rates.JPY ? (1 / rates.JPY) * 100 : null },
      { flag: 'https://flagcdn.com/cn.svg', pair: '¥1', zar: inv(rates.CNY) },
    ];
  }, [rates]);

  return (
    <div className="glass-panel p-3">
      <div className="text-xs text-gray-400 mb-2">FX (ZAR conversions)</div>
      {err && <div className="text-xs text-red-300 mb-2">{err}</div>}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
        {rows.map((r, i) => (
          <div key={i} className="flex items-center gap-2 bg-white/5 rounded px-2 py-1">
            <img src={r.flag} alt="flag" className="w-4 h-3 rounded-sm" />
            <div className="text-xs text-white/90">{r.pair}</div>
            <div className="ml-auto text-xs text-white font-semibold">R{r.zar != null ? r.zar.toFixed(2) : '--'}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CurrencyTicker;