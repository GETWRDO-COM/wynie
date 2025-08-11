import React, { useEffect, useMemo, useState } from 'react';

// Fetch ZAR base rates and display conversions of 1 USD/EUR/GBP/JPY(100)/CNY to ZAR
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
      try {
        const r = await fetchPrimary();
        setRates(r);
      } catch {
        const r = await fetchFallback();
        setRates(r);
      }
    } catch (e) {
      setErr('FX unavailable');
    }
  };

  useEffect(() => {
    fetchRates();
    const id = setInterval(fetchRates, 60_000);
    return () => clearInterval(id);
  }, []);

  const items = useMemo(() => {
    if (!rates) return [];
    const inv = (x) => (x ? 1 / x : null);
    const usd = inv(rates.USD);
    const eur = inv(rates.EUR);
    const gbp = inv(rates.GBP);
    const jpy = inv(rates.JPY);
    const cny = inv(rates.CNY);
    return [
      { code: 'USD', flagSrc: 'https://flagcdn.com/us.svg', label: '$1', value: usd },
      { code: 'EUR', flagSrc: 'https://flagcdn.com/eu.svg', label: '€1', value: eur },
      { code: 'GBP', flagSrc: 'https://flagcdn.com/gb.svg', label: '£1', value: gbp },
      { code: 'JPY', flagSrc: 'https://flagcdn.com/jp.svg', label: '¥100', value: jpy != null ? jpy * 100 : null },
      { code: 'CNY', flagSrc: 'https://flagcdn.com/cn.svg', label: '¥1', value: cny },
    ];
  }, [rates]);

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {items.map((it) => (
        <div key={it.code} className="px-2 py-1 rounded-lg text-xs text-white/90 border border-white/10 flex items-center gap-1" style={{ background: 'linear-gradient(135deg, color-mix(in_oklab, var(--brand-start) 12%, transparent), color-mix(in_oklab, var(--brand-end) 12%, transparent))' }}>
          <img src={it.flagSrc} alt={it.code} className="w-3.5 h-3.5 rounded-sm" />
          <span className="mr-1">{it.label}</span>
          <span>= R{it.value != null ? it.value.toFixed(2) : '--'}</span>
        </div>
      ))}
      {err && <div className="text-xs text-red-300">{err}</div>}
    </div>
  );
};

export default CurrencyTicker;