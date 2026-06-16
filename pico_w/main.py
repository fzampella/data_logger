import gc
import time

import machine
import network
import ntptime
import urequests

from secrets import API_URL, SOURCE, WIFI_PASSWORD, WIFI_SSID


SAMPLE_INTERVAL_SECONDS = 60
SEND_INTERVAL_SECONDS = 15 * 60
ADC_MAX = 4095
ADC_REFERENCE_VOLTS = 3.3
STATUS_LED = machine.Pin("LED", machine.Pin.OUT)
ADC_CHANNELS = (
    ("Battery", machine.ADC(27), 2.05),
    ("Solar Panel", machine.ADC(28), 10.765),
)
MAX_UNSENT_MEASUREMENTS = 24 * 60 * len(ADC_CHANNELS)


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
    return wlan


def disconnect_wifi(wlan):
    if wlan:
        wlan.disconnect()
        wlan.active(False)
    STATUS_LED.off()


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


def trim_unsent_measurements(unsent_measurements):
    overflow = len(unsent_measurements) - MAX_UNSENT_MEASUREMENTS
    if overflow > 0:
        del unsent_measurements[:overflow]


def post_measurements(measurements):
    response = None
    try:
        response = urequests.post(
            API_URL,
            json=measurements,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code >= 300:
            raise RuntimeError(
                "API returned {}: {}".format(response.status_code, response.text)
            )
    finally:
        if response:
            response.close()


def send_unsent_measurements(unsent_measurements):
    if not unsent_measurements:
        return

    wlan = None
    try:
        wlan = connect_wifi()
        post_measurements(unsent_measurements)
        print("sent {} queued measurements".format(len(unsent_measurements)))
        unsent_measurements.clear()
        STATUS_LED.on()
    finally:
        disconnect_wifi(wlan)


def sleep_until_next_sample(start_ms):
    elapsed_ms = time.ticks_diff(time.ticks_ms(), start_ms)
    sleep_ms = max(0, SAMPLE_INTERVAL_SECONDS * 1000 - elapsed_ms)
    STATUS_LED.off()
    machine.lightsleep(sleep_ms)


def main():
    wlan = None
    try:
        wlan = connect_wifi()
        sync_clock()
    finally:
        disconnect_wifi(wlan)

    unsent_measurements = []
    last_send_ms = time.ticks_ms()

    while True:
        sample_started_ms = time.ticks_ms()
        try:
            unsent_measurements.extend(read_measurements())
            trim_unsent_measurements(unsent_measurements)
            print("{} measurements waiting".format(len(unsent_measurements)))

            if time.ticks_diff(sample_started_ms, last_send_ms) >= SEND_INTERVAL_SECONDS * 1000:
                try:
                    send_unsent_measurements(unsent_measurements)
                finally:
                    last_send_ms = time.ticks_ms()
        except Exception as exc:
            STATUS_LED.off()
            print("sample/send failed:", exc)

        gc.collect()
        sleep_until_next_sample(sample_started_ms)


main()
