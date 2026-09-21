# Data Logger

A small Python module project managed with [`uv`](https://docs.astral.sh/uv/).

## Getting Started

```bash
cp .env.example .env
docker compose up --build
```

Open the dashboard:

```bash
http://localhost:8000/
```

The API container listens on port `8000`. Docker Compose exposes that as host
port `8000` by default. To expose a different host port:

```bash
API_PORT=8001 docker compose up --build
```

Then open:

```bash
http://localhost:8001/
```

For local development without Dockerizing the API:

```bash
uv sync
docker compose up -d db
uv run data-logger
```

## Database

This project includes a Dockerized PostgreSQL database for storing logged data.

```bash
cp .env.example .env
docker compose up -d db
```

The database starts with a `measurements` table:

- `unixtime_ms`: Unix timestamp in milliseconds, stored as `BIGINT`
- `adc`: ADC reading, stored as `SMALLINT`
- `v_out`: output voltage, stored as `DOUBLE PRECISION`
- `sensor`: sensor identifier, stored as `TEXT`
- `source`: data source identifier, stored as `TEXT`

Connection string:

```bash
postgresql://data_logger:data_logger_password@localhost:5432/data_logger
```

Inside Docker Compose, the API connects to the database service with host `db`:

```bash
postgresql://data_logger:data_logger_password@db:5432/data_logger
```

## API

Start the full Docker stack:

```bash
docker compose up --build
```

The API is exposed on host port `8000` by default:

```bash
http://localhost:8000/
```

To expose a different host port while keeping the container port at `8000`:

```bash
API_PORT=8001 docker compose up --build
```

For local development, start only the database and run the API with `uv`:

```bash
docker compose up -d db
uv run data-logger
```

To run local development on a different port:

```bash
PORT=8001 uv run data-logger
```

By default the API binds to `0.0.0.0`, so other machines on the same network can access it with:

```bash
http://YOUR_MACHINE_IP:8000/
```

The dashboard plots values over time, grouped by `sensor`, with controls for:

- `source`
- sensor checkboxes
- `v_out` or `adc`
- `1 hour`
- `1 day`
- `1 week`
- `1 month`

The chart automatically rescales to the selected sensor checkboxes. Hover over a point to inspect its timestamp, sensor, source, ADC value, and voltage. If present, `pico_w` appears first in the source dropdown.

The dashboard also includes a delete section. It uses the same protected delete API and requires the `DELETE_MEASUREMENTS_PASSWORD` value from `.env`.

Submit a measurement:

```bash
curl -X POST http://localhost:8000/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "unixtime_ms": 1718200000000,
    "adc": 1234,
    "v_out": 1.23,
    "sensor": "temperature_probe",
    "source": "bench_test"
}'
```

Submit multiple measurements in one request:

```bash
curl -X POST http://localhost:8000/measurements/bulk \
  -H "Content-Type: application/json" \
  -d '[
    {
      "unixtime_ms": 1718200000000,
      "adc": 1234,
      "v_out": 1.23,
      "sensor": "Battery",
      "source": "pico_w"
    },
    {
      "unixtime_ms": 1718200000000,
      "adc": 2345,
      "v_out": 2.34,
      "sensor": "Solar Panel",
      "source": "pico_w"
    }
  ]'
```

Health check:

```bash
curl http://localhost:8000/health
```

Delete measurements for one source/sensor over a time period:

```bash
curl -X DELETE 'http://localhost:8000/measurements?source=test&sensor=synthetic&start_unixtime_ms=1718200000000&end_unixtime_ms=1718203600000' \
  -H "X-Delete-Password: your-delete-password"
```

Set `DELETE_MEASUREMENTS_PASSWORD` in `.env` before using the delete endpoint.

To stop the stack:

```bash
docker compose down
```

## Portainer

You can deploy this project in Portainer as a stack.

Recommended options:

- Use a Git repository stack so Portainer can access this repository and build
  the `api` image from the included `Dockerfile`.
- Or build and push the API image to a registry, then replace `build: .` in
  `docker-compose.yml` with `image: your-registry/data-logger:latest`.

Set these stack environment variables in Portainer if you want values other
than the defaults:

```env
API_PORT=8000
POSTGRES_DB=data_logger
POSTGRES_USER=data_logger
POSTGRES_PASSWORD=data_logger_password
DELETE_MEASUREMENTS_PASSWORD=change-me
```

Port mapping is explicit:

```yaml
ports:
  - "${API_PORT:-8000}:8000"
```

That maps host port `API_PORT` to container port `8000`.

## Development

```bash
uv run python -m data_logger
```

## Raspberry Pi Pico W

The `pico_w/` folder contains a MicroPython client that reads Pico W ADC1 and ADC2 once per minute and posts them to the measurements API.

Pico W ADC channels:

- `adc1`: GPIO 27, physical pin 32
- `adc2`: GPIO 28, physical pin 34

Set up the Pico files:

```bash
cp pico_w/secrets.example.py pico_w/secrets.py
```

Edit `pico_w/secrets.py`:

```python
WIFI_SSID = "your-wifi-name"
WIFI_PASSWORD = "your-wifi-password"
API_URL = "http://YOUR_MACHINE_IP:8001/measurements/bulk"
SOURCE = "pico_w"
```

Run the API so the Pico can reach it:

```bash
API_PORT=8001 docker compose up --build
```

Allow the Pico through UFW, replacing `PICO_IP` with its network address:

```bash
sudo ufw allow from PICO_IP to any port 8001 proto tcp comment 'Pico W data logger'
```

Copy these files to the Pico W:

- `pico_w/main.py` as `main.py`
- `pico_w/secrets.py` as `secrets.py`

The Pico samples once per minute, stores unsent readings in RAM, wakes Wi-Fi every 15 minutes, syncs time, sends all queued readings in one request, turns Wi-Fi off again, and uses light sleep between samples. Measurement timestamps are calculated from `ticks_ms()` using the latest Unix-time sync bias, so timestamps keep moving while the Pico is sleeping.

The Pico records two measurements per sample:

- `sensor = "Battery"`
- `sensor = "Solar Panel"`
- `source = SOURCE`
