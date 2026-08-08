import json
import os
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import URLError
from urllib.request import urlopen

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from app import WeatherHandler


class StubGeocodingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.end_headers()
        payload = {"results": [{"name": "Berlin", "country": "DE", "latitude": 52.52, "longitude": 13.405}]}
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, *args):
        return


class StubWeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.end_headers()
        payload = {"daily": {"time": ["2026-08-09"], "temperature_2m_mean": [21.3]}}
        self.wfile.write(json.dumps(payload).encode())

    def log_message(self, *args):
        return


class WeatherApiTests(unittest.TestCase):
    def setUp(self):
        self.geocoding_server = HTTPServer(('127.0.0.1', 0), StubGeocodingHandler)
        self.weather_server = HTTPServer(('127.0.0.1', 0), StubWeatherHandler)
        self.geocoding_port = self.geocoding_server.server_address[1]
        self.weather_port = self.weather_server.server_address[1]
        threading.Thread(target=self.geocoding_server.serve_forever, daemon=True).start()
        threading.Thread(target=self.weather_server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.geocoding_server.shutdown()
        self.weather_server.shutdown()

    def _wait_for_server(self, process, url):
        deadline = time.time() + 10
        last_error = None
        while time.time() < deadline:
            if process.poll() is not None:
                stderr = process.stderr.read().decode('utf-8', errors='ignore')
                raise RuntimeError(f'Server exited early: {stderr}')
            try:
                with urlopen(url, timeout=1) as response:
                    return response.read().decode('utf-8')
            except (URLError, ConnectionRefusedError, TimeoutError) as exc:
                last_error = exc
                time.sleep(0.2)
        raise RuntimeError(f'Server did not become ready: {last_error}')

    def test_health_endpoint(self):
        process = subprocess.Popen([sys.executable, 'app.py'], cwd='python-service', env={**os.environ, 'PORT': '3203'}, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            body_text = self._wait_for_server(process, 'http://127.0.0.1:3203/api/health')
            body = json.loads(body_text)
            self.assertEqual(body['status'], 'ok')
        finally:
            process.terminate()
            process.wait(timeout=5)

    def test_weather_endpoint(self):
        process = subprocess.Popen(
            [sys.executable, 'app.py'],
            cwd='python-service',
            env={
                **os.environ,
                'PORT': '3204',
                'GEOCODING_PROVIDER_URL': f'http://127.0.0.1:{self.geocoding_port}',
                'WEATHER_PROVIDER_URL': f'http://127.0.0.1:{self.weather_port}'
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            body_text = self._wait_for_server(process, 'http://127.0.0.1:3204/api/weather?location=Berlin')
            body = json.loads(body_text)
            self.assertEqual(body['location']['name'], 'Berlin')
            self.assertEqual(body['weather']['average_temperature_c'], 21.3)
        finally:
            process.terminate()
            process.wait(timeout=5)

    def test_location_with_spaces_is_supported(self):
        handler = WeatherHandler.__new__(WeatherHandler)
        self.assertEqual(handler._build_url('https://example.com', {'name': 'New York'}), 'https://example.com?name=New+York')


if __name__ == '__main__':
    unittest.main()
