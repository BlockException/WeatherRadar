const http = require('node:http');
const { URL } = require('node:url');

const port = Number(process.env.PORT || 3000);
const geocodingProviderUrl = process.env.GEOCODING_PROVIDER_URL || 'https://geocoding-api.open-meteo.com/v1/search';
const weatherProviderUrl = process.env.WEATHER_PROVIDER_URL || 'https://api.open-meteo.com/v1/forecast';

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, { 'content-type': 'application/json' });
  res.end(JSON.stringify(payload));
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
}

async function buildWeatherResponse(location) {
  const geocodingUrl = new URL(geocodingProviderUrl);
  geocodingUrl.searchParams.set('name', location);
  geocodingUrl.searchParams.set('count', '1');
  geocodingUrl.searchParams.set('language', 'en');
  geocodingUrl.searchParams.set('format', 'json');

  const geocodingData = await fetchJson(geocodingUrl.toString());
  const result = geocodingData.results?.[0];
  if (!result) {
    throw new Error('Location not found');
  }

  const weatherUrl = new URL(weatherProviderUrl);
  weatherUrl.searchParams.set('latitude', result.latitude);
  weatherUrl.searchParams.set('longitude', result.longitude);
  weatherUrl.searchParams.set('daily', 'temperature_2m_mean');
  weatherUrl.searchParams.set('timezone', 'auto');
  weatherUrl.searchParams.set('forecast_days', '1');

  const weatherData = await fetchJson(weatherUrl.toString());
  const temperatures = weatherData.daily?.temperature_2m_mean || [];
  const averageTemperature = temperatures[0] ?? null;

  return {
    location: {
      name: result.name,
      country: result.country,
      latitude: result.latitude,
      longitude: result.longitude
    },
    weather: {
      average_temperature_c: averageTemperature,
      source: 'Open-Meteo'
    }
  };
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  if (req.method === 'GET' && url.pathname === '/api/health') {
    return sendJson(res, 200, { status: 'ok', service: 'javascript' });
  }

  if (req.method === 'GET' && url.pathname === '/api/weather') {
    const location = url.searchParams.get('location')?.trim();
    if (!location) {
      return sendJson(res, 400, { error: 'location query parameter is required' });
    }

    try {
      const payload = await buildWeatherResponse(location);
      return sendJson(res, 200, payload);
    } catch (error) {
      return sendJson(res, 404, { error: error.message || 'Unable to resolve location' });
    }
  }

  return sendJson(res, 404, { error: 'Not Found' });
});

server.listen(port, () => {
  console.log(`JavaScript service listening on port ${port}`);
});
