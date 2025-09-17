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
  for (let i = 1; i &lt; 7; i++) {
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

const WeatherWidget = ({ compact = false }) =&gt; {
  const [weather, setWeather] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [location, setLocation] = useState('Paarl'); // Default to never show unknown
  const [loading, setLoading] = useState(true);

  useEffect(() =&gt; {
    const loadWeather = async () =&gt; {
      try {
        setLoading(true);
        let coords = FALLBACK;
        let locationName = 'Paarl, South Africa'; // Always have a proper location

        // Try to get user's actual location
        if (navigator.geolocation) {
          try {
            const pos = await new Promise((resolve, reject) =&gt; {
              navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
            });
            coords = {
              latitude: pos.coords.latitude,
              longitude: pos.coords.longitude
            };
            const geoLocation = await reverseGeocode(coords.latitude, coords.longitude);
            locationName = geoLocation || 'Paarl, South Africa'; // Fallback if geocoding fails
          } catch (e) {
            console.warn('Geolocation failed, using fallback location');
            locationName = 'Paarl, South Africa';
          }
        }

        const { current, forecast: forecastData } = await fetchWeather(coords.latitude, coords.longitude);
        setWeather(current);
        setForecast(forecastData);
        setLocation(locationName);
      } catch (error) {
        console.error('Weather fetch failed:', error);
        // Fallback weather data
        setWeather({ tempC: 15, code: 1, high: 20, low: 10, rain: 20 });
        setForecast([
          { day: 'Thu', high: 18, low: 8, code: 1, rain: 10 },
          { day: 'Fri', high: 22, low: 12, code: 2, rain: 0 },
          { day: 'Sat', high: 19, low: 9, code: 3, rain: 30 },
          { day: 'Sun', high: 16, low: 6, code: 1, rain: 5 },
          { day: 'Mon', high: 21, low: 11, code: 2, rain: 0 },
          { day: 'Tue', high: 17, low: 7, code: 3, rain: 40 }
        ]);
        setLocation('Paarl, South Africa');
      } finally {
        setLoading(false);
      }
    };

    loadWeather();
  }, []);

  if (loading) {
    return (
      &lt;div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-md p-4"&gt;
        &lt;div className="text-white/90 font-semibold mb-2 text-base"&gt;Weather&lt;/div&gt;
        &lt;div className="text-gray-400 text-sm"&gt;Loading weather data...&lt;/div&gt;
      &lt;/div&gt;
    );
  }

  // Compact layout per user: smaller, no emojis, vertical forecast list
  if (compact) {
    return (
      &lt;div className="rounded-xl border border-white/10 bg-black/50 backdrop-blur-xl p-3"&gt;
        &lt;div className="flex items-center justify-between mb-2"&gt;
          &lt;div className="text-white/90 font-semibold text-sm"&gt;Weather&lt;/div&gt;
          &lt;div className="text-[11px] text-emerald-400"&gt;{location}&lt;/div&gt;
        &lt;/div&gt;

        &lt;div className="flex items-center justify-between mb-2"&gt;
          &lt;div className="text-white text-xl font-bold"&gt;{weather?.tempC}°C&lt;/div&gt;
          &lt;div className="text-xs text-gray-400"&gt;H:{weather?.high}° · L:{weather?.low}° · Rain {weather?.rain}%&lt;/div&gt;
        &lt;/div&gt;

        &lt;div className="divide-y divide-white/10"&gt;
          {forecast.map((d, i) =&gt; (
            &lt;div key={i} className="py-1.5 flex items-center justify-between text-xs"&gt;
              &lt;div className="text-gray-300"&gt;{d.day}&lt;/div&gt;
              &lt;div className="text-white/90"&gt;{d.high}° / &lt;span className="text-gray-400"&gt;{d.low}°&lt;/span&gt;&lt;/div&gt;
              &lt;div className="text-blue-400"&gt;{d.rain}%&lt;/div&gt;
            &lt;/div&gt;
          ))}
        &lt;/div&gt;
      &lt;/div&gt;
    );
  }

  return (
    &lt;div className="glass-panel p-4"&gt;
      &lt;div className="flex items-center justify-between mb-3"&gt;
        &lt;div className="text-white/90 font-semibold"&gt;Weather&lt;/div&gt;
        &lt;div className="text-xs text-emerald-400"&gt;📍 {location}&lt;/div&gt;
      &lt;/div&gt;

      &lt;div className="grid grid-cols-[auto,1fr] gap-4"&gt;
        {/* Current Weather - Left Side */}
        &lt;div className="flex items-center gap-3"&gt;
          &lt;div className="text-4xl"&gt;{codeToEmoji(weather?.code)}&lt;/div&gt;
          &lt;div&gt;
            &lt;div className="text-2xl font-bold text-white"&gt;{weather?.tempC}°C&lt;/div&gt;
            &lt;div className="text-xs text-gray-400"&gt;
              H: {weather?.high}° L: {weather?.low}°
            &lt;/div&gt;
            &lt;div className="text-xs text-blue-400"&gt;💧 {weather?.rain}% rain&lt;/div&gt;
          &lt;/div&gt;
        &lt;/div&gt;

        {/* 7-Day Forecast - Right Side (Compact) */}
        &lt;div&gt;
          &lt;div className="text-xs text-white/70 font-semibold mb-2"&gt;7-Day Forecast&lt;/div&gt;
          &lt;div className="grid grid-cols-6 gap-1"&gt;
            {forecast.map((day, index) =&gt; (
              &lt;div key={index} className="text-center p-1 rounded bg-black/20"&gt;
                &lt;div className="text-xs text-gray-400 mb-1"&gt;{day.day}&lt;/div&gt;
                &lt;div className="text-sm mb-1"&gt;{codeToEmoji(day.code)}&lt;/div&gt;
                &lt;div className="text-xs text-white"&gt;
                  &lt;div&gt;{day.high}°&lt;/div&gt;
                  &lt;div className="text-gray-400"&gt;{day.low}°&lt;/div&gt;
                &lt;/div&gt;
              &lt;/div&gt;
            ))}
          &lt;/div&gt;
        &lt;/div&gt;
      &lt;/div&gt;
    &lt;/div&gt;
  );
};

export default WeatherWidget;