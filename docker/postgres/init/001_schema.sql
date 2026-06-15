CREATE TABLE IF NOT EXISTS measurements (
    unixtime_ms BIGINT NOT NULL,
    adc SMALLINT NOT NULL,
    v_out DOUBLE PRECISION NOT NULL,
    sensor TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_measurements_unixtime_ms
    ON measurements (unixtime_ms DESC);

CREATE INDEX IF NOT EXISTS idx_measurements_sensor_source
    ON measurements (sensor, source);
