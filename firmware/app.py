import sys
import time
import gc

from modem import A7670
from temperature import read_temperature
from measuerment_db import MeasurementDB
from water_level import get_water_level
from current_sensor import init_current_sensor, read_current_sensor
from sleep_minus import sleep_minus
from blink import blink
import config

def main():
    init_current_sensor()
    modem = A7670()
    modem.wait_ready()

    # initialize the time from the network
    modem.sync_network_time()
    t = time.localtime()
    print(f"UTC time: {t[0]}-{t[1]}-{t[2]} {t[3]}:{t[4]}:{t[5]}")

    to_upload = []

    db = MeasurementDB()
    db.write("meta", reboot=True)
    initial = True

    while True:
        for i in range(1 if initial else 60): # upload once per hour
            if initial:
                initial = False
            else:
                sleep_minus(60)  # one measurement per minute
            
            temperature = read_temperature()
            water_level = get_water_level()
            V, mA, pump_percent = read_current_sensor()
            db.write(
                "sensors",
                temperature=temperature,
                water_level=water_level,
                V=V, mA=mA, pump_percent=pump_percent,
            )
            blink()

        try:
            modem.turn_on()
            modem.wait_ready()
            modem.sync_network_time()
            upload_queue_len = len(to_upload)
            db.write(
                "meta",
                dBm=modem.signal_quality(),
                mem_free=gc.mem_free(),
                upload_queue_len=upload_queue_len,
            )
            to_upload.append(db.get_compressed_data())
            to_upload = to_upload[-5:]  # limit queue to 5 chunks
            for data in to_upload:
                modem.send_http_request(
                    "POST",
                    config.url,
                    headers=dict(**{"Content-Encoding": "gzip"}, **config.auth_headers),
                    data=data,
                )
                db.write("meta", bytes_sent=len(data) + 663)
                # overhead of one http request in this setup is ~663 bytes
                to_upload.remove(data)

            modem.turn_off()
            blink("ll")
            print("# Upload successful")
        except Exception as e:
            blink("slslslslsl")
            print("# Error during upload:")
            sys.print_exception(e)
            modem.turn_off()

        print(f"mem_free: {gc.mem_free() / 1024}kB")
        gc.collect()
