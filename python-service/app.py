import os
from typing import Any
from urllib.parse import parse_qs, parse_qsl, quote_plus, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get('PORT', '3001'))
GEOCODING_PROVIDER_URL = os.environ.get('GEOCODING_PROVIDER_URL', 'https://geocoding-api.open-meteo.com/v1/search')
WEATHER_PROVIDER_URL = os.environ.get('WEATHER_PROVIDER_URL', 'https://api.open-meteo.com/v1/forecast')


class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == '/api/health':
            self._send_json(200, {'status': 'ok', 'service': 'python'})
            return

        if parsed.path == '/api/weather':
            params = parse_qs(parsed.query)
            location = (params.get('location', [''])[0] or '').strip()
            if not location:
                self._send_json(400, {'error': 'location query parameter is required'})
                return

            try:
                payload = self._build_weather_payload(location)
                self._send_json(200, payload)
            except Exception as exc:
                self._send_json(404, {'error': str(exc) or 'Unable to resolve location'})
            return

        self._send_json(404, {'error': 'Not Found'})

    def _build_weather_payload(self, location: str) -> dict[str, Any]:
        geocoding_url = self._build_url(GEOCODING_PROVIDER_URL, {'name': location, 'count': '1', 'language': 'en', 'format': 'json'})
        geocoding_data = self._fetch_json(geocoding_url)
        result = (geocoding_data.get('results') or [{}])[0]
        if not result:
            raise ValueError('Location not found')

        weather_url = self._build_url(WEATHER_PROVIDER_URL, {'latitude': str(result['latitude']), 'longitude': str(result['longitude']), 'daily': 'temperature_2m_mean', 'timezone': 'auto', 'forecast_days': '1'})
        weather_data = self._fetch_json(weather_url)
        temperatures = (weather_data.get('daily') or {}).get('temperature_2m_mean') or []

        return {
            'location': {
                'name': result['name'],
                'country': result.get('country'),
                'latitude': result.get('latitude'),
                'longitude': result.get('longitude')
            },
            'weather': {
                'average_temperature_c': temperatures[0] if temperatures else None,
                'source': 'Open-Meteo'
            }
        }

    def _build_url(self, base_url: str, params: dict[str, str]) -> str:
        parsed = urlparse(base_url)
        existing_params = parse_qsl(parsed.query, keep_blank_values=True)
        merged_params = dict(existing_params)
        merged_params.update(params)
        query = urlencode(merged_params, quote_via=quote_plus)
        return urlunparse(parsed._replace(query=query))

    def _fetch_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={'User-Agent': 'js-py-backend/1.0'})
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode('utf-8')
        self.send_response(status)
        self.send_header('content-type', 'application/json')
        self.send_header('content-length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


if __name__ == '__main__':
    HTTPServer(('0.0.0.0', PORT), WeatherHandler).serve_forever()
