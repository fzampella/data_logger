from time import time
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field
from psycopg import Error as PsycopgError

from data_logger.dashboard import DASHBOARD_HTML
from data_logger.db import insert_measurement, list_measurements, list_sources

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


app = FastAPI(title="Data Logger API")


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
