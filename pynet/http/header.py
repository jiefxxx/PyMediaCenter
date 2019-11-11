from urllib.parse import urlparse, parse_qsl

from pynet.http.tools import http_parse_query, http_parse_field


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


class Url:
    def __init__(self, full_path):
        self.full = full_path
        self._parsed = urlparse(full_path)
        self.path = self._parsed.path
        self.query = parse_qsl(self._parsed.query)

    def get(self, key, default=None):
        for query in self.query:
            if query[0] == key:
                return query[1]
        return default

    def to_sql_where(self, blacklist=None):
        if blacklist is None:
            blacklist = []
        where = {}
        for query in self.query:
            if query[0] not in blacklist:
                where[query[0]] = query[1]
                if query[1] == 'null':
                    where[query[0]] = None

        return where

    def __str__(self):
        return self.full
