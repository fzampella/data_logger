import os
from typing import Protocol, TypedDict

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


load_dotenv()


DEFAULT_DATABASE_URL = (
    "postgresql://data_logger:data_logger_password@localhost:5432/data_logger"
)


class Measurement(Protocol):
    unixtime_ms: int
    adc: int
    v_out: float
    sensor: str
    source: str


class MeasurementRow(TypedDict):
    unixtime_ms: int
    adc: int
    v_out: float
    sensor: str
    source: str


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def insert_measurement(measurement: Measurement) -> None:
    with psycopg.connect(get_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO measurements (
                    unixtime_ms,
                    adc,
                    v_out,
                    sensor,
                    source
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    measurement.unixtime_ms,
                    measurement.adc,
                    measurement.v_out,
                    measurement.sensor,
                    measurement.source,
                ),
            )


def list_sources() -> list[str]:
    with psycopg.connect(get_database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT source
                FROM measurements
                ORDER BY source
                """
            )
            return [row[0] for row in cursor.fetchall()]


def list_measurements(source: str, since_unixtime_ms: int) -> list[MeasurementRow]:
    with psycopg.connect(get_database_url(), row_factory=dict_row) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    unixtime_ms,
                    adc,
                    v_out,
                    sensor,
                    source
                FROM measurements
                WHERE source = %s
                  AND unixtime_ms >= %s
                ORDER BY unixtime_ms ASC, sensor ASC
                """,
                (source, since_unixtime_ms),
            )
            return list(cursor.fetchall())
