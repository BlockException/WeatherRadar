const test = require('node:test');
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const http = require('node:http');
const { once } = require('node:events');

function startStubServer(handler) {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve(server);
    });
  });
}

test('returns health status', async () => {
  const child = spawn(process.execPath, ['server.js'], {
    cwd: __dirname + '/..',
    env: { ...process.env, PORT: '3201' },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  child.stdout.on('data', () => {});
  child.stderr.on('data', () => {});

  await new Promise((resolve) => setTimeout(resolve, 400));

  const response = await fetch('http://127.0.0.1:3201/api/health');
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.status, 'ok');

  child.kill();
  await once(child, 'exit');
});

test('returns weather information from a location', async () => {
  const geocodingServer = await startStubServer((req, res) => {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ results: [{ name: 'Berlin', country: 'DE', latitude: 52.52, longitude: 13.405 }], generationtime_ms: 1 }));
  });

  const weatherServer = await startStubServer((req, res) => {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ daily: { time: ['2026-08-09'], temperature_2m_mean: [21.3] } }));
  });

  const child = spawn(process.execPath, ['server.js'], {
    cwd: __dirname + '/..',
    env: {
      ...process.env,
      PORT: '3202',
      GEOCODING_PROVIDER_URL: `http://127.0.0.1:${geocodingServer.address().port}`,
      WEATHER_PROVIDER_URL: `http://127.0.0.1:${weatherServer.address().port}`
    },
    stdio: ['ignore', 'pipe', 'pipe']
  });

  await new Promise((resolve) => setTimeout(resolve, 400));

  const response = await fetch('http://127.0.0.1:3202/api/weather?location=Berlin');
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.location.name, 'Berlin');
  assert.equal(body.weather.average_temperature_c, 21.3);

  child.kill();
  await once(child, 'exit');
  geocodingServer.close();
  weatherServer.close();
});
