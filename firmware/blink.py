from machine import Pin
from time import sleep

led = Pin(25, Pin.OUT)

def blink(desc='s'):
    for char in desc:
        if char == 's':
            led.on()
            sleep(0.05)
            led.off()
            sleep(0.1)
        elif char == 'l':
            led.on()
            sleep(0.25)
            led.off()
            sleep(0.25)