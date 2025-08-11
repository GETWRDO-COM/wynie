import React, { useEffect, useState } from 'react';

// Open-Meteo free API (no key). We'll geolocate user; fallback to Paarl.
const FALLBACK_COORDS = { lat: -33.734, lon: 18.962 }; // Paarl

function codeToEmoji(code) {
  // Simplified mapping of weather codes
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
  const [loc, setLoc] = useState(null);

  useEffect(() => {
    const getWeather = async (coords) => {
      const { latitude, longitude } = coords || {};
      const lat = latitude ?? FALLBACK_COORDS.lat;
      const lon = longitude ?? FALLBACK_COORDS.lon;
      try {
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code&timezone=auto`;
        const resp = await fetch(url);
        const json = await resp.json();
        setData(json?.current);
        setLoc({ lat, lon, tz: json?.timezone });
      } catch (e) {
        setData(null);
      }
    };

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => getWeather(pos.coords),
        () => getWeather(null),
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
      );
    } else {
      getWeather(null);
    }
  }, []);

  if (!data) return <div className="glass-panel p-3 text-xs text-gray-300">Weather: -- °C</div>;

  return (
    <div className="glass-panel px-4 py-3 flex items-center gap-3">
      <div className="text-2xl">{codeToEmoji(data.weather_code)}</div>
      <div>
        <div className="text-xs text-gray-400">Current Weather</div>
        <div className="text-white font-semibold">{Math.round(data.temperature_2m)}°C</div>
      </div>
    </div>
  );
};

export default WeatherWidget;