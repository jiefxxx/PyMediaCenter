import http
import io
import re
import time
from urllib.parse import urlparse, parse_qsl


def http_code_to_string(code):
    for el in http.HTTPStatus:
        if el.value == code:
            return el.phrase
    return ""


def http_parse_query(line):
    match = re.match(r"(.*) (.*) (.*)", line.decode())
    if match is not None:
        return match.group(1), match.group(2), match.group(3)
    else:
        raise Exception("Invalid Request", str(line))


def http_parse_field(line):
    match = re.match(r"(.*): (.*)", line.decode())
    if match is not None:
        return match.group(1), match.group(2)
    else:
        raise Exception("Invalid format field:", str(line))


class Url:
    def __init__(self, full_path):
        self.full = full_path
        self._parsed = urlparse(full_path)
        self.path = self._parsed.path
        self.query = parse_qsl(self._parsed.query)

    def __str__(self):
        return self.full


class HTTPFields:
    def __init__(self):
        self.fields = []

    def get(self, name, default=None):
        for field_name, field_value in self.fields:
            if field_name == name:
                return field_value
        return default

    def set(self, name, value):
        self.fields.append((name, value))

    def append(self, value):
        self.fields.append(value)

    def __str__(self):
        ret = ""
        for field in self.fields:
            ret += field[0] + ": " + str(field[1]) + "\r\n"
        return ret


class HTTPHeader:
    def __init__(self):
        self.url = None
        self.query = None
        self.protocol = None
        self.fields = HTTPFields()

    def parse_line(self, line):
        if self.query is None:
            self.query, url, self.protocol = http_parse_query(line)
            self.url = Url(url)
        else:
            self.fields.append(http_parse_field(line))

    def __str__(self):
        ret = str(self.query)+" "+str(self.url)+" "+str(self.protocol)+"\r\n"
        ret += str(self.fields)
        ret += "\r\n"
        return ret


class HTTPData:
    def __init__(self, size):
        self.size = size
        self.current_size = 0
        if self.size > 100 * 1024:
            self.data_stream_type = "file"
            self.data_stream = open("/tmp/python_http." + str(time.time()) + ".tmp", "wb")
        else:
            self.data_stream_type = "memory"
            self.data_stream = io.BytesIO()

    def __str__(self):
        return "HTTPData(size=" + str(self.size) + ", data_stream=" + \
               self.data_stream_type + ", completed=" + str(self.completed())

    def completed(self):
        return self.current_size == self.size

    def feed(self, data):
        if not self.current_size == self.size:
            split_index = self.size - self.current_size
            if len(data) > split_index:
                self.current_size += len(data[:split_index])
                self.write(data[:split_index])
                ret = data[split_index:]
            else:
                self.current_size += len(data)
                self.write(data)
                ret = []

            if self.completed():
                self.data_stream.seek(0)

            return ret
        return data

    def write(self, data):
        self.data_stream.write(data)

    def read(self, size=-1):
        return self.data_stream.read(size)


class HTTPRequest:
    def __init__(self):
        self.header = HTTPHeader()
        self.data = None
        self.header_completed = False

    def feed(self, data):
        while b'\r\n' in data and not self.header_completed:
            line, data = data.split(b'\r\n', 1)
            if len(line) == 0:
                self.on_header_completed()
                self.header_completed = True
            else:
                self.header.parse_line(line)

        if self.header_completed and self.data is not None and not self.data.completed():
            data = self.data.feed(data)

        return data

    def completed(self):
        if self.header_completed:
            if self.data is None or self.data.completed():
                return True
        return False

    def on_header_completed(self):
        data_length = int(self.header.fields.get("Content-Length", default='0'))
        if data_length > 0:
            self.data = HTTPData(data_length)


class HTTPResponse:
    def __init__(self):
        self.proto = "HTTP/1.1"
        self.code = 404
        self.fields = HTTPFields()
        self.fields.set("Server", "Python-test/0.02")

    def __str__(self):
        ret = self.proto+" "+str(self.code)+" "+http_code_to_string(self.code)+"\r\n"
        ret += str(self.fields)
        ret += "\r\n"
        return ret
