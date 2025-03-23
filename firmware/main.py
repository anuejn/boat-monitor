from machine import UART, Pin
import sys
import time
import gc

from modem import A7670
from temperature import read_temperature
from measuerment_db import MeasurementDB
from sleep_minus import sleep_minus
from blink import blink
import config

modem = A7670()
modem.wait_ready()

# initialize the time from the network
modem.sync_network_time()
t = time.localtime()
print(f"UTC time: {t[0]}-{t[1]}-{t[2]} {t[3]}:{t[4]}:{t[5]}")

to_upload = []

db = MeasurementDB()
while True:
    for i in range(10):
        temperature = read_temperature()
        db.write("sensors", temperature=temperature)
        blink()
        sleep_minus(6)
    
    to_upload.append(db.get_compressed_data())
    to_upload = to_upload[-5:]  # limit to 5 measurements

    try:
        modem.turn_on()
        modem.wait_ready()
        upload_queue_len = len(to_upload)
        for data in to_upload:
            modem.send_http_request(
                "POST", 
                config.url, 
                headers=dict(**{"Content-Encoding": "gzip"}, **config.auth_headers),
                data=data,
            )
            # overhead of one http request in this setup is ~663 bytes
            to_upload.remove(data)
        db.write("cellular", bytes=len(data) + 663, dBm=modem.signal_quality(), mem_free=gc.mem_free(), upload_queue_len=upload_queue_len)
        modem.sync_network_time()
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
