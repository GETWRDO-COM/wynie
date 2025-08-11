import React, { useEffect, useState } from 'react';

const FALLBACK_COORDS = { latitude: -33.734, longitude: 18.962 }; // Paarl

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

const WeatherWidget = () => {
  const [data, setData] = useState(null);
  const [place, setPlace] = useState('');

  const fetchAll = async (coords) => {
    const { latitude, longitude } = coords || FALLBACK_COORDS;
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&forecast_days=1&timezone=auto`;
      const resp = await fetch(url);
      const json = await resp.json();
      const current = json?.current;
      const daily = json?.daily;
      const meta = { tz: json?.timezone };
      // Reverse geocode for name
      const geoResp = await fetch(`https://geocoding-api.open-meteo.com/v1/reverse?latitude=${latitude}&longitude=${longitude}&language=en`);
      const geo = await geoResp.json();
      const name = geo?.results?.[0]?.name || 'Current Location';

      setPlace(name);
      setData({
        tempC: Math.round(current?.temperature_2m ?? 0),
        code: current?.weather_code,
        high: Math.round(daily?.temperature_2m_max?.[0] ?? 0),
        low: Math.round(daily?.temperature_2m_min?.[0] ?? 0),
        rain: Math.round(daily?.precipitation_probability_max?.[0] ?? 0),
      });
    } catch (e) {
      setData(null);
    }
  };

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => fetchAll(pos.coords),
        () => fetchAll(null),
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
      );
    } else {
      fetchAll(null);
    }
  }, []);

  if (!data) return <div className="glass-panel p-3 text-xs text-gray-300">Weather: -- °C</div>;

  return (
    <div className="glass-panel px-4 py-3 flex items-center gap-3">
      <div className="text-2xl">{codeToEmoji(data.code)}</div>
      <div>
        <div className="text-xs text-gray-400">{place}</div>
        <div className="text-white font-semibold">{data.tempC}°C • H {data.high}° • L {data.low}° • {data.rain}% rain</div>
      </div>
    </div>
  );
};

export default WeatherWidget;