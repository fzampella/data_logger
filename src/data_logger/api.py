import os
from secrets import compare_digest
from time import time
from typing import Annotated, Literal

from fastapi import FastAPI, Header, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from psycopg import Error as PsycopgError

from data_logger.dashboard import DASHBOARD_HTML
from data_logger.db import (
    delete_measurements,
    insert_measurement,
    list_measurements,
    list_sources,
)

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1
INT16_MIN = -(2**15)
INT16_MAX = 2**15 - 1
RangeName = Literal["1h", "1d", "1w", "1m"]
RANGE_TO_MILLISECONDS: dict[RangeName, int] = {
    "1h": 60 * 60 * 1000,
    "1d": 24 * 60 * 60 * 1000,
    "1w": 7 * 24 * 60 * 60 * 1000,
    "1m": 31 * 24 * 60 * 60 * 1000,
}


class MeasurementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    unixtime_ms: Annotated[int, Field(ge=INT64_MIN, le=INT64_MAX)]
    adc: Annotated[int, Field(ge=INT16_MIN, le=INT16_MAX)]
    v_out: float
    sensor: Annotated[str, Field(min_length=1)]
    source: Annotated[str, Field(min_length=1)]


class MeasurementCreated(BaseModel):
    status: str


class MeasurementRead(BaseModel):
    unixtime_ms: int
    adc: int
    v_out: float
    sensor: str
    source: str


class MeasurementsDeleted(BaseModel):
    deleted_rows: int


app = FastAPI(title="Data Logger API")


def get_delete_measurements_password() -> str | None:
    return os.getenv("DELETE_MEASUREMENTS_PASSWORD")


def verify_delete_password(header_password: str | None) -> None:
    expected_password = get_delete_measurements_password()
    if not expected_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Delete password is not configured",
        )

    if not header_password or not compare_digest(header_password, expected_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid delete password",
        )


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return DASHBOARD_HTML


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/measurements",
    response_model=MeasurementCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_measurement(measurement: MeasurementCreate) -> MeasurementCreated:
    try:
        insert_measurement(measurement)
    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return MeasurementCreated(status="created")


@app.delete("/measurements", response_model=MeasurementsDeleted)
def delete_sensor_measurements(
    source: Annotated[str, Query(min_length=1)],
    sensor: Annotated[str, Query(min_length=1)],
    start_unixtime_ms: Annotated[int, Query(ge=INT64_MIN, le=INT64_MAX)],
    end_unixtime_ms: Annotated[int, Query(ge=INT64_MIN, le=INT64_MAX)],
    x_delete_password: Annotated[
        str | None,
        Header(alias="X-Delete-Password"),
    ] = None,
) -> MeasurementsDeleted:
    verify_delete_password(x_delete_password)

    if start_unixtime_ms > end_unixtime_ms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_unixtime_ms must be less than or equal to end_unixtime_ms",
        )

    try:
        deleted_rows = delete_measurements(
            source=source,
            sensor=sensor,
            start_unixtime_ms=start_unixtime_ms,
            end_unixtime_ms=end_unixtime_ms,
        )
    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return MeasurementsDeleted(deleted_rows=deleted_rows)


@app.get("/api/sources", response_model=list[str])
def get_sources() -> list[str]:
    try:
        return list_sources()
    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc


@app.get("/api/measurements", response_model=list[MeasurementRead])
def get_measurements(
    source: Annotated[str, Query(min_length=1)],
    range: RangeName = "1h",
) -> list[MeasurementRead]:
    since_unixtime_ms = int(time() * 1000) - RANGE_TO_MILLISECONDS[range]

    try:
        return [
            MeasurementRead(**measurement)
            for measurement in list_measurements(source, since_unixtime_ms)
        ]
    except PsycopgError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
