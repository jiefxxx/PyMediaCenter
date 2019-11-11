import io
import json
import os
from tempfile import NamedTemporaryFile


class HTTPData:
    def __init__(self, size):
        self.size = size
        self.current_size = 0

        if self.size > 100 * 1024:
            self.data_stream = NamedTemporaryFile(mode="w+b")
        else:
            self.data_stream = io.BytesIO()

    def io_size(self):
        if isinstance(self.data_stream, io.BytesIO):
            return self.data_stream.getbuffer().nbytes
        else:
            return os.stat(self.data_stream.name).st_size

    def completed(self):
        return self.io_size() == self.size

    def feed(self, data):
        if self.io_size()+len(data) > self.size:
            raise Exception("too much data")
        self.data_stream.write(data)

        if self.completed():
            self.seek()

    def close(self):
        self.data_stream.close()

    def __str__(self):
        return "HTTPData(size=" + str(os.fstat(self.data_stream.fileno()).st_size) + "/" + \
               str(self.size) + \
               ", completed=" + str(self.completed()) + ")"

    def read(self, size=-1):
        return self.data_stream.read(size)

    def seek(self, n=0):
        self.data_stream.seek(n)

    def json(self):
        return json.loads(self.read())
