# Data Logger

A small Python module project managed with [`uv`](https://docs.astral.sh/uv/).

## Getting Started

```bash
uv sync
cp .env.example .env
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

## API

Start the API:

```bash
uv run data-logger
```

To run on a different port:

```bash
PORT=8001 uv run data-logger
```

By default the API binds to `0.0.0.0`, so other machines on the same network can access it with:

```bash
http://YOUR_MACHINE_IP:8000/
```

For a different port:

```bash
PORT=8001 uv run data-logger
```

To override the bind address explicitly:

```bash
HOST=0.0.0.0 PORT=8001 uv run data-logger
```

Open the dashboard:

```bash
http://localhost:8000/
```

The dashboard plots values over time, grouped by `sensor`, with controls for:

- `source`
- `v_out` or `adc`
- `1 hour`
- `1 day`
- `1 week`
- `1 month`

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

Health check:

```bash
curl http://localhost:8000/health
```

To stop the database:

```bash
docker compose down
```

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
API_URL = "http://YOUR_MACHINE_IP:8001/measurements"
SOURCE = "pico_w"
```

Run the API so the Pico can reach it:

```bash
HOST=0.0.0.0 PORT=8001 uv run data-logger
```

Allow the Pico through UFW, replacing `PICO_IP` with its network address:

```bash
sudo ufw allow from PICO_IP to any port 8001 proto tcp comment 'Pico W data logger'
```

Copy these files to the Pico W:

- `pico_w/main.py` as `main.py`
- `pico_w/secrets.py` as `secrets.py`

The Pico posts two measurements per minute:

- `sensor = "adc1"`
- `sensor = "adc2"`
- `source = SOURCE`
