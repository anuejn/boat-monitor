import os
import socketserver

import serial
from serial.tools.list_ports import comports

serialport = None

class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("-> Connected")
        while True:
            try:
                self.request.setblocking(0)
                from_socket = self.request.recv(1024)
                if len(from_socket) == 0:  # the socket is closed
                    print("\n-> Socket closed\n\n")
                    break
                serialport.write(from_socket)
            except BlockingIOError:
                pass
            from_device = serialport.read(1024)
            if len(from_device) > 0:    
                print(from_device.decode(), end="")
                self.request.sendall(from_device)

if __name__ == "__main__":
    device = None
    for port in comports():
        if "usb" in port.device:
            device = port.device
            break
    if device is None:
        print("No USB device found")
        exit(1)
    print(f"Using device {device}")
    serialport = serial.Serial(device, 115200, timeout=0)

    port = int(os.getenv('SERIAL_SERVER_PORT'))
    print(f"Starting server on port {port}")
    with socketserver.TCPServer(("localhost", port), TCPHandler) as server:
        server.allow_reuse_address = True
        server.allow_reuse_port = True
        server.serve_forever()
