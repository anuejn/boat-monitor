import time
import machine


class ATError(Exception):
    pass


class TimeoutError(Exception):
    pass


class A7670:
    def __init__(self, timeout=5):
        self.uart = machine.UART(
            0,
            115200,
            timeout=timeout,
            timeout_char=timeout,
            tx=machine.Pin(16),
            rx=machine.Pin(17),
        )
        self.pwrkey_pin = machine.Pin(18, machine.Pin.OUT)
        self.pwrkey_pin.value(1)
        self.timeout = timeout

        self.turn_on()

    def turn_off(self):
        self.pwrkey_pin.value(0)
        time.sleep(3)
        self.pwrkey_pin.value(1)

    def turn_on(self, timeout=20):
        self.pwrkey_pin.value(0)
        time.sleep(0.1)
        self.pwrkey_pin.value(1)
        while self.uart.any():
            self.uart.read(1)
        self.uart.write(b"AT\r\n")
        start_time = time.time()
        while True:
            try:
                line = self._readline(timeout=1)
                print("modem:", line)
                if line.startswith(b"OK"):
                    time.sleep(1)
                    break
            except TimeoutError:
                self.uart.write(b"AT\r\n")
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout during initial AT command")

    def _readline(self, timeout=None) -> bytes:
        if timeout is None:
            timeout = self.timeout
        start_time = time.time()
        while True:
            line = self.uart.readline()
            if line:
                print("modem:", line)
                return line
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout while waiting for line to come through")

    def _at_cmd(self, cmd, return_extra_data=False):
        full_cmd = f"AT+{cmd}\r\n"
        print(f"host : AT+{cmd}")
        self.uart.write(full_cmd.encode())
        response = ""
        extra_data = ""
        start_time = time.time()
        while True:
            if time.time() - start_time > self.timeout:
                raise TimeoutError("Timeout after sending 'AT' command " + full_cmd)
            line = self._readline().decode().strip()
            if line == "OK" or line == "DOWNLOAD":
                if return_extra_data:
                    return response, extra_data
                else:
                    return response
            elif line == "ERROR":
                raise ATError(f"during {full_cmd}. " + response)

            end = len(cmd)
            end = cmd.find("=") if "=" in cmd else end
            end = cmd.find("?") if "?" in cmd else end
            cmd_base = cmd[:end]
            expected_prefix = f"+{cmd_base}: "
            if line == full_cmd.strip():
                pass  # ignore the echo
            elif line.startswith(expected_prefix):
                response += line[len(expected_prefix) :]
            else:
                extra_data += line + "\n"

    def _parse_comma_response(self, response, field=0, mapper=int):
        parts = response.split(",")
        if isinstance(mapper, dict) or isinstance(mapper, list):
            mapper_fn = lambda x: mapper[int(x)]
        else:
            mapper_fn = mapper
        to_return = mapper_fn(parts[field])
        return to_return
    
    def wait_ready(self):
        start_time = time.time()
        while True:
            try:
                self.is_ready()
                break
            except Exception as e:
                print(e)
                if time.time() - start_time > 60:
                    raise TimeoutError("Timeout while waiting for modem to become ready")
                time.sleep(1)

    def is_ready(self):
        assert self.sim_card_status() == "READY", "SIM card not ready"
        print(f"signal: {self.signal_quality()}dBm")
        assert self.network_registration() == "READY", "Network registration failed"
        assert "Online" in self.ue_system_information(), "UE not online"

    def send_http_request(self, method, url, data=None, headers={}, timeout=10):
        start_time = time.time()
        # terminate all maybe existing requests
        try:
            self._at_cmd("HTTPTERM")
        except Exception as e:
            pass

        # setup the request
        self._at_cmd("CGDCONT")
        self._at_cmd("HTTPINIT")
        self._at_cmd(f'HTTPPARA="URL","{url}"')
        method_code = {
            "GET": 0,
            "POST": 1,
            "PUT": 2,
            "DELETE": 3,
        }[method]

        for key, value in headers.items():
            self._at_cmd(f'HTTPPARA="USERDATA","{key}: {value}"')

        if data:
            self._at_cmd(f"HTTPDATA={len(data)},10")
            self.uart.write(data)
            start_time = time.time()
            while not self._readline().startswith(b"OK"):
                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout after sending HTTP data")
                pass

        # this actually sends the request
        self._at_cmd(f"HTTPACTION={method_code}")

        # wait for the response
        start_time = time.time()
        while True:
            line = self._readline().decode().strip()
            prefix = "+HTTPACTION: "
            if line.startswith(prefix):
                payload = line[len(prefix) :]
                status_code = int(payload.split(",")[1])
                datalen = payload.split(",")[2]
                break
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout while waiting for HTTP response")

        # read the response
        from time import sleep

        sleep(1)
        _, header = self._at_cmd("HTTPHEAD", return_extra_data=True)
        if datalen != "0" and datalen != "chunked":
            body_lenth = self._parse_comma_response(self._at_cmd("HTTPREAD?"), 1)
            self._at_cmd(f"HTTPREAD=0,{body_lenth}")
            start_time = time.time()
            while not self._readline().startswith(b"+HTTPREAD: "):
                if time.time() - start_time > timeout:
                    raise TimeoutError("Timeout while reading HTTP response")
            body = self.uart.read(body_lenth)
        else:
            body = None
        self._at_cmd("HTTPTERM")

        print(f"HTTP request took {time.time() - start_time:.2f}s")
        return status_code, header, body

    def sync_network_time(self):
        self._at_cmd("CTZU=1")
        time_string = self._at_cmd("CCLK?").strip('"')
        date_part, time_part = time_string.split(",")
        if "+" in time_part:
            time_part, tz = time_part.split("+")
            tz = int(tz)
        else:
            time_part, tz = time_part.split("-")
            tz = -int(tz)
        year, month, day = [int(x) for x in date_part.split("/")]
        year += 2000
        hour, minute, second = [int(x) for x in time_part.split(":")]
        unix_timestamp = time.mktime(
            (year, month, day, hour, minute, second, None, None)
        )
        unix_timestamp -= tz * 60 * 15
        year, month, day, hour, minute, second, _, _ = time.localtime(unix_timestamp)
        machine.RTC().datetime((year, month, day, None, hour, minute, second, None))

    def sim_card_status(self):
        return self._at_cmd("CPIN?")

    def signal_quality(self):
        csq = self._parse_comma_response(self._at_cmd("CSQ"), field=0)
        assert csq != 99, "no signal"
        return -113 + (2 * csq)  # dBm

    def network_registration(self):
        options = [
            "SEARCHING",  # 'not registered, ME is not currently searching an operator to register to',
            "READY",  # 'registered, home network',
            "SEARCHING",  # 'registered, but ME is currently trying to attach or searching an operator to register to',
            "FAILED",  # 'registration denied',
            "FAILED",  # 'unknown',
            "READY",  # 'registered, roaming',
            "FAILED",  # 'registered for "SMS only, home network',
        ]
        return self._parse_comma_response(
            self._at_cmd("CREG?"), field=1, mapper=options
        )

    def ue_system_information(self):
        return self._at_cmd("CPSI?")

    def pdp_information(self):
        return self._at_cmd("CGACT?")
