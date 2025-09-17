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
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code&forecast_days=7&timezone=auto`;
  const resp = await fetch(url);
  const json = await resp.json();
  
  // Current weather
  const current = {
    tempC: Math.round(json?.current?.temperature_2m ?? 0),
    code: json?.current?.weather_code,
    high: Math.round(json?.daily?.temperature_2m_max?.[0] ?? 0),
    low: Math.round(json?.daily?.temperature_2m_min?.[0] ?? 0),
    rain: Math.round(json?.daily?.precipitation_probability_max?.[0] ?? 0),
  };
  
  // 7-day forecast
  const forecast = [];
  for (let i = 1; i < 7; i++) {
    forecast.push({
      day: new Date(Date.now() + i * 24 * 60 * 60 * 1000).toLocaleDateString('en-US', { weekday: 'short' }),
      high: Math.round(json?.daily?.temperature_2m_max?.[i] ?? 0),
      low: Math.round(json?.daily?.temperature_2m_min?.[i] ?? 0),
      code: json?.daily?.weather_code?.[i],
      rain: Math.round(json?.daily?.precipitation_probability_max?.[i] ?? 0),
    });
  }
  
  return { current, forecast };
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
  const [weather, setWeather] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [location, setLocation] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadWeather = async () => {
      try {
        setLoading(true);
        let coords = FALLBACK;
        let locationName = FALLBACK.name;

        // Try to get user's actual location
        if (navigator.geolocation) {
          try {
            const pos = await new Promise((resolve, reject) => {
              navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
            });
            coords = {
              latitude: pos.coords.latitude,
              longitude: pos.coords.longitude
            };
            locationName = await reverseGeocode(coords.latitude, coords.longitude);
          } catch (e) {
            console.warn('Geolocation failed, using fallback:', e);
          }
        }

        const { current, forecast: forecastData } = await fetchWeather(coords.latitude, coords.longitude);
        setWeather(current);
        setForecast(forecastData);
        setLocation(locationName);
      } catch (error) {
        console.error('Weather fetch failed:', error);
        setWeather({ tempC: 15, code: 1, high: 20, low: 10, rain: 20 });
        setForecast([]);
        setLocation('Paarl');
      } finally {
        setLoading(false);
      }
    };

    loadWeather();
  }, []);

  if (loading) {
    return (
      <div className="rounded-xl border border-white/10 bg-neutral-800/50 backdrop-blur-sm p-4">
        <div className="text-white/90 font-semibold mb-2">Weather</div>
        <div className="text-gray-400 text-sm">Loading weather data...</div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-white/5 to-white/[0.02] backdrop-blur-md p-6 hover:from-white/10 hover:to-white/[0.05] transition-all duration-300">
      <div className="flex items-center justify-between mb-4">
        <div className="text-white/90 font-semibold text-lg">Weather</div>
        <div className="text-xs text-emerald-400 font-medium">📍 {location}</div>
      </div>

      <div className="grid grid-cols-[auto,1fr] gap-6">
        {/* Current Weather - Left Side */}
        <div className="flex items-center gap-4">
          <div className="text-5xl">{codeToEmoji(weather?.code)}</div>
          <div>
            <div className="text-3xl font-light text-white mb-1">{weather?.tempC}°C</div>
            <div className="text-sm text-gray-300 font-medium mb-1">
              H: {weather?.high}° L: {weather?.low}°
            </div>
            <div className="text-xs text-blue-400 font-medium">💧 {weather?.rain}% rain</div>
          </div>
        </div>

        {/* 7-Day Forecast - Right Side (Compact) */}
        <div>
          <div className="text-sm text-white/70 font-semibold mb-3">7-Day Forecast</div>
          <div className="grid grid-cols-7 gap-1">
            {forecast.map((day, index) => (
              <div key={index} className="text-center p-1.5 rounded-lg bg-black/20 hover:bg-black/30 transition-colors">
                <div className="text-xs text-gray-400 mb-1 font-medium">{day.day}</div>
                <div className="text-sm mb-1">{codeToEmoji(day.code)}</div>
                <div className="text-xs text-white font-medium">
                  <div>{day.high}°</div>
                  <div className="text-gray-400">{day.low}°</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Timestamp - Bottom Right */}
      <div className="flex justify-end mt-4">
        <div className="text-xs text-gray-400 font-medium">
          Last Update 1 min ago | {new Date().toLocaleDateString('en-ZA', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })} | {new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}
        </div>
      </div>
    </div>
  );
};

export default WeatherWidget;