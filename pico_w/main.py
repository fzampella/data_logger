import gc
import time

import machine
import network
import ntptime
import urequests

from secrets import API_URL, SOURCE, WIFI_PASSWORD, WIFI_SSID


SAMPLE_INTERVAL_SECONDS = 60
ADC_MAX = 4095
ADC_REFERENCE_VOLTS = 3.3
STATUS_LED = machine.Pin("LED", machine.Pin.OUT)
ADC_CHANNELS = (
    ("Battery", machine.ADC(27), 2.05),
    ("Solar Panel", machine.ADC(28), 10.765),
)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    timeout_at = time.time() + 30
    while not wlan.isconnected():
        STATUS_LED.toggle()
        time.sleep(0.5)
        if time.time() > timeout_at:
            raise RuntimeError("Timed out connecting to Wi-Fi")

    STATUS_LED.on()
    print("Wi-Fi connected:", wlan.ifconfig())


def sync_clock():
    for attempt in range(3):
        try:
            ntptime.settime()
            print("Clock synced")
            return
        except Exception as exc:
            print("Clock sync failed:", exc)
            time.sleep(2 + attempt)

    raise RuntimeError("Could not sync clock with NTP")


def unix_time_ms():
    return int(time.time() * 1000)


def adc_to_volts(adc):
    return adc * ADC_REFERENCE_VOLTS / ADC_MAX


def read_measurements():
    timestamp_ms = unix_time_ms()
    measurements = []

    for sensor, adc_channel, gain in ADC_CHANNELS:
        adc = adc_channel.read_u16() >> 4
        measurements.append(
            {
                "unixtime_ms": timestamp_ms,
                "adc": adc,
                "v_out": adc_to_volts(adc) * gain,
                "sensor": sensor,
                "source": SOURCE,
            }
        )

    return measurements


def post_measurement(measurement):
    response = None
    try:
        response = urequests.post(
            API_URL,
            json=measurement,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                "API returned {}: {}".format(response.status_code, response.text)
            )
    finally:
        if response:
            response.close()


def sleep_until_next_sample(start_ms):
    elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ms)
    sleep_ms = max(0, SAMPLE_INTERVAL_SECONDS * 1000 - elapsed_ms)
    time.sleep_ms(sleep_ms)


def main():
    connect_wifi()
    sync_clock()

    while True:
        sample_started_ms = time.ticks_ms()
        try:
            for measurement in read_measurements():
                post_measurement(measurement)
                print("sent", measurement)
            STATUS_LED.on()
        except Exception as exc:
            STATUS_LED.off()
            print("send failed:", exc)

        gc.collect()
        sleep_until_next_sample(sample_started_ms)


main()
