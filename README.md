# JS & Python Backend Reference Project

[![CI](https://github.com/your-username/js-py-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/js-py-backend/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org)
[![Node.js](https://img.shields.io/badge/node-18%2B-green)](https://nodejs.org)
[![License](https://img.shields.io/badge/license-MIT-yellow)](https://opensource.org/licenses/MIT)

This repository contains a clean reference implementation of a dual-language backend that resolves a location and returns the average temperature for the current day using public APIs.

## Features

- JavaScript service with a REST API
- Python service with the same API contract
- Geocoding lookup for any location in the world
- Weather retrieval from Open-Meteo
- Health checks for monitoring
- GitHub Actions CI and Dependabot configuration

## API

### Health

Request:

```bash
curl http://localhost:3000/api/health
```

Response:

```json
{
  "status": "ok",
  "service": "javascript"
}
```

### Weather

Request:

```bash
curl "http://localhost:3000/api/weather?location=Berlin"
```

Response:

```json
{
  "location": {
    "name": "Berlin",
    "country": "DE",
    "latitude": 52.52,
    "longitude": 13.405
  },
  "weather": {
    "average_temperature_c": 21.3,
    "source": "Open-Meteo"
  }
}
```

## Run the JavaScript service

```bash
cd js-service
npm install
npm start
```

## Run the Python service

```bash
cd python-service
python app.py
```

## Test the services

```bash
cd js-service
npm test
```

```bash
cd python-service
python -m pytest -q tests
```

## Project structure

```text
js-service/
  server.js
  tests/
python-service/
  app.py
  tests/
.github/
  workflows/ci.yml
  dependabot.yml
```

## API documentation

The API contract is documented in [openapi.yaml](openapi.yaml).

You can view it locally with any OpenAPI-compatible tool such as Swagger UI or Redoc.

## CI and automation

- GitHub Actions runs the JavaScript and Python test suites on every push and pull request.
- Dependabot checks the Node and Python dependencies weekly.
