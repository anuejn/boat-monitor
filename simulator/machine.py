# this file should not be copied to the target device
# it is used to mock the hardware for on computer testing

import time
import math

class UART:
    def __init__(self, n, baud):
        import socket
        s = socket.socket()
        import os
        port = int(os.getenv('SERIAL_SERVER_PORT'))
        addr_info = socket.getaddrinfo("localhost", port)
        s.connect(addr_info[0][-1])
        s.setblocking(False)
        self.s = s
        self.buffer = b''

    def write(self, data):
        self.s.write(data)

    def _fill_buffer(self):
        read = self.s.read()
        if read:
            self.buffer += read

    def read(self, bytes):
        while len(self.buffer) < bytes:
            self._fill_buffer()
        to_return = self.buffer[:bytes]
        self.buffer = self.buffer[bytes:]
        return to_return

    def readline(self):
        while b'\n' not in self.buffer:
            self._fill_buffer()
        pos = self.buffer.index(b'\n')
        to_return = self.buffer[:pos+1]
        self.buffer = self.buffer[pos+1:]
        return to_return
    
    def any(self):
        self._fill_buffer()
        return len(self.buffer) > 0

class ADC:
    def __init__(self, n):
        pass

    def read_u16(self):
        return int(math.sin(time.time()) * 32767 + 32767)

class RTC:
    @staticmethod
    def datetime(datetimetuple=None):
        if datetimetuple is None:
            return time.localtime()
        else:
            print("setting time to:", time.mktime(datetimetuple))
