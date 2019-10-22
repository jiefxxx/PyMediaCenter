import email.parser
import http
import io
import json
import os
import re
import time
from urllib.parse import urlparse, parse_qsl

from pynet.multipart import MultipartParser


def sql_where_from_url(url):
    where = {}
    for query in url.query:
        if query[1] == 'null':
            where[query[0]] = None
        else:
            where[query[0]] = query[1]
    return where

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
        ret = str(self.query) + " " + str(self.url) + " " + str(self.protocol) + "\r\n"
        ret += str(self.fields)
        ret += "\r\n"
        return ret


class HTTPDataAbstract:
    def __init__(self, size):
        self.size = size
        self.current_size = 0

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
                ret = b""

            if self.completed():
                self.on_completed()

            return ret
        return data

    def close(self):
        pass

    def on_completed(self):
        pass

    def write(self, data):
        pass

    def read(self, n=-1):
        return None


class HTTPData(HTTPDataAbstract):
    def __init__(self, size, boundary=None):
        HTTPDataAbstract.__init__(self, size)

        self.boundary = boundary
        self.multipart = False
        if self.boundary:
            self.multipart = True

        if self.size > 100 * 1024:
            self.data_stream_type = "file"
            self.data_stream = open("/tmp/python_http." + str(time.time()) + ".tmp", "wb+")
        else:
            self.data_stream_type = "memory"
            self.data_stream = io.BytesIO()

    def close(self):
        if self.data_stream_type == "file":
            name = self.data_stream.name
            self.data_stream.close()
            os.remove(name)
        else:
            self.data_stream.close()

    def __str__(self):
        return "HTTPData(size=" + str(self.size) + ", data_stream=" + \
               self.data_stream_type + ", completed=" + str(self.completed())

    def on_completed(self):
        self.data_stream.seek(0)

    def write(self, data):
        self.data_stream.write(data)

    def read(self, size=-1):
        return self.data_stream.read(size)

    def seek(self, n=0):
        self.data_stream.seek(n)

    def json(self):
        return json.loads(self.read())

    def get_multipart(self):
        if self.multipart:
            return MultipartParser(self.data_stream, self.boundary)
        else:
            raise Exception("Not multipart Data")

    def is_multipart(self):
        return self.multipart


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
        content_type = self.header.fields.get("Content-Type", default=None)
        if content_type:
            content_type = content_type.split('; ', 1)

        if data_length > 0:
            if content_type and content_type[0] == "multipart/form-data" and content_type[1][:9] == "boundary=":
                self.data = HTTPData(data_length, boundary=content_type[1][9:])
            else:
                self.data = HTTPData(data_length)

    def close(self):
        if self.data:
            self.data.close()


class HTTPResponse:
    def __init__(self):
        self.proto = "HTTP/1.1"
        self.code = 404
        self.fields = HTTPFields()
        self.fields.set("Server", "Python-test/0.02")

    def __str__(self):
        ret = self.proto + " " + str(self.code) + " " + http_code_to_string(self.code) + "\r\n"
        ret += str(self.fields)
        ret += "\r\n"
        return ret
