import React, { useEffect, useMemo, useState } from 'react';

// Fetch ZAR base rates and display conversions of 1 USD/EUR/GBP/JPY(100)/CNY to ZAR
const CurrencyTicker = () => {
  const [rates, setRates] = useState(null);
  const [err, setErr] = useState('');

  const fetchRates = async () => {
    try {
      setErr('');
      const resp = await fetch('https://api.exchangerate.host/latest?base=ZAR&symbols=USD,EUR,GBP,JPY,CNY');
      const data = await resp.json();
      if (!data || !data.rates) throw new Error('No rates');
      setRates(data.rates);
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
      { code: 'USD', flag: '🇺🇸', label: '$1', value: usd },
      { code: 'EUR', flag: '🇪🇺', label: '€1', value: eur },
      { code: 'GBP', flag: '🇬🇧', label: '£1', value: gbp },
      { code: 'JPY', flag: '🇯🇵', label: '¥100', value: jpy != null ? jpy * 100 : null },
      { code: 'CNY', flag: '🇨🇳', label: '¥1', value: cny },
    ];
  }, [rates]);

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {items.map((it, idx) => (
        <div key={it.code} className="px-2 py-1 rounded-lg text-xs text-white/90 border border-white/10" style={{ background: 'linear-gradient(135deg, color-mix(in_oklab, var(--brand-start) 12%, transparent), color-mix(in_oklab, var(--brand-end) 12%, transparent))' }}>
          <span className="mr-1">{it.flag}</span>
          <span className="mr-1">{it.label}</span>
          <span>= R{it.value != null ? it.value.toFixed(2) : '--'}</span>
        </div>
      ))}
      {err && <div className="text-xs text-red-300">{err}</div>}
    </div>
  );
};

export default CurrencyTicker;