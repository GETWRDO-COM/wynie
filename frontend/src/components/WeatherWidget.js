import React, { useEffect, useState } from 'react';

const FALLBACK = { latitude: -33.734, longitude: 18.962, name: 'Paarl' };

function codeToEmoji(code) {
  if ([0].includes(code)) return '☀️';
  if ([1, 2, 3].includes(code)) return '🌤️';
  if ([45, 48].includes(code)) return '🌫️';
  if ([51, 53, 55, 56, 57].includes(code)) return '🌦️';
  if ([61, 63, 65, 80, 81, 82].includes(code)) return '🌧️';
  if ([71, 73, 75, 77, 85, 86].includes(code)) return '❄️';
  if ([95, 96, 99].includes(code)) return '⛈️';
  return '🌡️';
}

async function fetchWeather(lat, lon) {
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&forecast_days=1&timezone=auto`;
  const resp = await fetch(url);
  const json = await resp.json();
  return {
    tempC: Math.round(json?.current?.temperature_2m ?? 0),
    code: json?.current?.weather_code,
    high: Math.round(json?.daily?.temperature_2m_max?.[0] ?? 0),
    low: Math.round(json?.daily?.temperature_2m_min?.[0] ?? 0),
    rain: Math.round(json?.daily?.precipitation_probability_max?.[0] ?? 0),
  };
}

async function reverseGeocode(lat, lon) {
  try {
    const r = await fetch(`https://geocoding-api.open-meteo.com/v1/reverse?latitude=${lat}&longitude=${lon}&language=en`);
    const j = await r.json();
    return j?.results?.[0]?.name || 'Unknown';
  } catch {
    return 'Unknown';
  }
}

const WeatherWidget = () => {
  const [data, setData] = useState(null);
  const [place, setPlace] = useState(FALLBACK.name);

  // Load fallback first, then try geolocation
  useEffect(() => {
    (async () => {
      try { const w = await fetchWeather(FALLBACK.latitude, FALLBACK.longitude); setData(w); }
      catch { setData({ tempC: 0, code: 1, high: 0, low: 0, rain: 0 }); }
    })();
  }, []);

  useEffect(() => {
    const tryGeo = async () => {
      if (!navigator.geolocation) return;
      navigator.geolocation.getCurrentPosition(async (pos) => {
        try { const { latitude, longitude } = pos.coords; const w = await fetchWeather(latitude, longitude); setData(w); const n = await reverseGeocode(latitude, longitude); setPlace(n); } catch {}
      });
    };
    tryGeo();
  }, []);

  if (!data) return <div className="glass-panel p-3 text-xs text-gray-300">Weather: -- °C</div>;

  return (
    <div className="glass-panel px-4 py-3 flex items-center gap-4">
      <div className="text-3xl leading-none">{codeToEmoji(data.code)}</div>
      <div className="flex-1">
        <div className="text-xs text-gray-400">Current Location</div>
        <div className="text-white text-sm font-semibold mb-1">{place}</div>
        <div className="text-white text-2xl font-bold">{data.tempC}°C</div>
        <div className="mt-2 flex flex-wrap gap-2">
          <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-xs text-white/90">H {data.high}°</span>
          <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-xs text-white/90">L {data.low}°</span>
          <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-xs text-white/90">{data.rain}% rain</span>
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;