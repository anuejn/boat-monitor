from machine import ADC, Pin

adc = ADC(Pin(27))
high_pin = Pin(26, Pin.OUT)

VAL_LOW  = 30420
VAL_HIGH = 53200
STICK_LENGTH = 35

LUT = [
    # real, measured
    (0, 0),
    (3.5, 7),
    (6.5, 12.9),
    (8.5, 14.7),
    (10.5, 16.4),
    (12.5, 18.1),
    (14.5, 19.5),
    (16.5, 21.0),
    (19, 22.4),
    (21.5, 23.8),
    (23.5, 25.0),
    (25.5, 26.31),
    (27.5, 27.51),
    (29.5, 29.5),
    (31.5, 31.5),
    (33, 33),
    (34, 35),
]

def lerp(x, x0, y0, x1, y1):
    if x < x0:
        return y0
    elif x > x1:
        return y1
    else:
        return y0 + (y1 - y0) * (x - x0) / (x1 - x0)

def correct_water_level(water_level):
    if water_level < 0:
        return 0
    elif water_level > STICK_LENGTH:
        return STICK_LENGTH
    else:
        for i in range(len(LUT) - 1):
            if LUT[i][1] <= water_level <= LUT[i + 1][1]:
                return lerp(water_level, LUT[i][1], LUT[i][0], LUT[i + 1][1], LUT[i + 1][0])
        return water_level

def get_water_level():
    high_pin.on()
    reading = 0
    for _ in range(256):
        reading += adc.read_u16()
    high_pin.off()
    reading /= 256
    uncorrected = STICK_LENGTH - (reading - VAL_LOW) / (VAL_HIGH - VAL_LOW) * STICK_LENGTH
    return correct_water_level(uncorrected)
