import io
import time

from deflate import DeflateIO, GZIP

class MeasurementDB:
        """A cass to represent a measurement database to be sent to an InfluxDB server.
        """
        def __init__(self, compress=True):
             self.compress = compress
             self.compressed = io.BytesIO()
             if self.compress:
                 self.input = DeflateIO(self.compressed, GZIP)
             else:
                 self.input = self.compressed

        def get_compressed_data(self):
            self.input.close()
            value = self.compressed.getvalue()

            # reset the buffer
            self.__init__(self.compress)
            
            return value

        def write(self, measurement: str, **kwargs):
            # encode the measurement into the InfluxDB line protocol
            fields_string = ",".join(f"{key}={value}" for key, value in kwargs.items())
            line = f"{measurement} {fields_string} {int(time.time())}\n"
            self.input.write(line.encode())
