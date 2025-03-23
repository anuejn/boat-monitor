import machine
import utime

# sensor_temp = machine.ADC(4)
conversion_factor = 3.3 / (65535)

def get_water_level():
    voltage = sensor_temp.read_u16() * conversion_factor
