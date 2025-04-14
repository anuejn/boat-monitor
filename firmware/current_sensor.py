from machine import Timer, I2C, Pin
from ina219 import INA219

current_threshold = 100

low_count = 0
high_count = 0
current_sum = 0

current_sensor = INA219(shunt_ohms=0.1, i2c=I2C(0, scl=Pin(21), sda=Pin(20)))


def init_current_sensor():
    Timer(-1, period=100, mode=Timer.PERIODIC, callback=_current_sensor_callback)
    current_sensor.configure()

def _current_sensor_callback(timer):
    current = current_sensor.current()
    global current_sum, high_count, low_count
    current_sum += current
    if current > current_threshold:
        high_count += 1
    else:
        low_count += 1

def read_current_sensor():
    voltage = current_sensor.voltage()
    global current_sum, high_count, low_count
    V=voltage
    mA=current_sum/(high_count+low_count)
    pump_percent=high_count/(high_count+low_count) * 100
    low_count = 0
    high_count = 0
    current_sum = 0
    return V, mA, pump_percent
