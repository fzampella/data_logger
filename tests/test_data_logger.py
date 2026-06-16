import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from data_logger import get_host, get_port
from data_logger.api import (
    MeasurementCreate,
    create_measurement,
    create_measurements,
    dashboard,
    delete_sensor_measurements,
    get_measurements,
    get_sources,
    health,
)


def test_create_measurement(monkeypatch):
    inserted_measurements = []

    def fake_insert_measurement(measurement):
        inserted_measurements.append(measurement)

    monkeypatch.setattr("data_logger.api.insert_measurement", fake_insert_measurement)

    response = create_measurement(
        MeasurementCreate(
            unixtime_ms=1718200000000,
            adc=1234,
            v_out=1.23,
            sensor="temperature_probe",
            source="bench_test",
        )
    )

    assert response.status == "created"
    assert len(inserted_measurements) == 1
    assert inserted_measurements[0].sensor == "temperature_probe"


def test_create_measurement_rejects_out_of_range_adc():
    with pytest.raises(ValidationError):
        MeasurementCreate(
            unixtime_ms=1718200000000,
            adc=32768,
            v_out=1.23,
            sensor="temperature_probe",
            source="bench_test",
        )


def test_create_measurements_bulk(monkeypatch):
    inserted_batches = []

    def fake_insert_measurements(measurements):
        inserted_batches.append(measurements)
        return len(measurements)

    monkeypatch.setattr("data_logger.api.insert_measurements", fake_insert_measurements)

    response = create_measurements(
        [
            MeasurementCreate(
                unixtime_ms=1718200000000,
                adc=1234,
                v_out=1.23,
                sensor="Battery",
                source="pico_w",
            ),
            MeasurementCreate(
                unixtime_ms=1718200000000,
                adc=2345,
                v_out=2.34,
                sensor="Solar Panel",
                source="pico_w",
            ),
        ]
    )

    assert response.inserted_rows == 2
    assert inserted_batches[0][0].sensor == "Battery"


def test_health():
    assert health() == {"status": "ok"}


def test_dashboard_contains_controls():
    html = dashboard()

    assert "Data Logger Dashboard" in html
    assert 'id="sourceSelect"' in html
    assert 'id="metricSelect"' in html
    assert 'value="v_out" selected' in html
    assert 'value="adc"' in html
    assert 'value="1h"' in html
    assert 'value="1m"' in html
    assert 'id="deleteSensorSelect"' in html
    assert 'id="deletePasswordInput"' in html
    assert 'id="deleteButton"' in html


def test_get_sources(monkeypatch):
    monkeypatch.setattr("data_logger.api.list_sources", lambda: ["bench", "field"])

    assert get_sources() == ["bench", "field"]


def test_get_measurements_uses_selected_source_and_range(monkeypatch):
    calls = []

    def fake_list_measurements(source, since_unixtime_ms):
        calls.append((source, since_unixtime_ms))
        return [
            {
                "unixtime_ms": 1718200000000,
                "adc": 1234,
                "v_out": 1.23,
                "sensor": "temperature_probe",
                "source": source,
            }
        ]

    monkeypatch.setattr("data_logger.api.time", lambda: 1718203600)
    monkeypatch.setattr("data_logger.api.list_measurements", fake_list_measurements)

    measurements = get_measurements(source="bench_test", range="1h")

    assert calls == [("bench_test", 1718200000000)]
    assert measurements[0].v_out == 1.23


def test_delete_sensor_measurements(monkeypatch):
    calls = []

    def fake_delete_measurements(source, sensor, start_unixtime_ms, end_unixtime_ms):
        calls.append((source, sensor, start_unixtime_ms, end_unixtime_ms))
        return 12

    monkeypatch.setenv("DELETE_MEASUREMENTS_PASSWORD", "secret")
    monkeypatch.setattr("data_logger.api.delete_measurements", fake_delete_measurements)

    response = delete_sensor_measurements(
        source="test",
        sensor="synthetic",
        start_unixtime_ms=1718200000000,
        end_unixtime_ms=1718203600000,
        x_delete_password="secret",
    )

    assert response.deleted_rows == 12
    assert calls == [("test", "synthetic", 1718200000000, 1718203600000)]


def test_delete_sensor_measurements_rejects_bad_password(monkeypatch):
    monkeypatch.setenv("DELETE_MEASUREMENTS_PASSWORD", "secret")

    with pytest.raises(HTTPException) as exc_info:
        delete_sensor_measurements(
            source="test",
            sensor="synthetic",
            start_unixtime_ms=1718200000000,
            end_unixtime_ms=1718203600000,
            x_delete_password="wrong",
        )

    assert exc_info.value.status_code == 401


def test_delete_sensor_measurements_requires_configured_password(monkeypatch):
    monkeypatch.delenv("DELETE_MEASUREMENTS_PASSWORD", raising=False)

    with pytest.raises(HTTPException) as exc_info:
        delete_sensor_measurements(
            source="test",
            sensor="synthetic",
            start_unixtime_ms=1718200000000,
            end_unixtime_ms=1718203600000,
            x_delete_password="secret",
        )

    assert exc_info.value.status_code == 503


def test_delete_sensor_measurements_rejects_invalid_time_range(monkeypatch):
    monkeypatch.setenv("DELETE_MEASUREMENTS_PASSWORD", "secret")

    with pytest.raises(HTTPException) as exc_info:
        delete_sensor_measurements(
            source="test",
            sensor="synthetic",
            start_unixtime_ms=1718203600000,
            end_unixtime_ms=1718200000000,
            x_delete_password="secret",
        )

    assert exc_info.value.status_code == 400


def test_get_port_uses_default(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)

    assert get_port() == 8000


def test_get_port_uses_environment(monkeypatch):
    monkeypatch.setenv("PORT", "8001")

    assert get_port() == 8001


def test_get_host_uses_lan_accessible_default(monkeypatch):
    monkeypatch.delenv("HOST", raising=False)

    assert get_host() == "0.0.0.0"


def test_get_host_uses_environment(monkeypatch):
    monkeypatch.setenv("HOST", "127.0.0.1")

    assert get_host() == "127.0.0.1"
