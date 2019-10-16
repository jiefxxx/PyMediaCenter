import http
import re
from urllib.parse import urlparse, parse_qsl

STATE_NO_DATA = 0
STATE_DATA    = 1
STATE_HEADER  = 2
STATE_COMPLET = 3

class Url():
    def __init__(self, full_path):
        self.full = full_path
        self._parsed = urlparse(full_path)
        self.path = self._parsed.path
        self.query = parse_qsl(self._parsed.query)

    def __str__(self):
        return "Url( path: '"+str(self.path)+"', query: "+str(self.query)+" )"

class Http_proto():
    def __init__(self):
        self.fields = []
        self.data = b''

    def get_field(self,name,default=None):
        for field_name,field_value in self.fields:
            if field_name == name:
                return field_value
        return default

    def set_field(self,name,data):
        for field in self.fields:
            if field[0] == name:
                self.fields.remove(field)
        field = (name,data)
        self.fields.append(field)

    def set_data(self,data,content_type="text/text"):
        self.set_field("Content-type",content_type)
        if(type(data) is str):
            self.data = data.encode()
        elif(type(data) is bytes):
            self.data = data
        self.set_field("Content-length",str(len(self.data)))


class Request(Http_proto):
    def __init__(self):
        Http_proto.__init__(self)
        self.methode = None
        self.url = None
        self.query = None
        self.protocol = None

        self.state = 0

        self.data_length = 0

    def feed(self,data):
        while len(data)>0:
            if self.state == STATE_NO_DATA:
                data = self._feed_no_data(data)
            elif self.state == STATE_HEADER:
                data = self._feed_request(data)
            elif self.state == STATE_DATA:
                data = self._feed_data(data)
            elif self.state == STATE_COMPLET:
                return data
        return data

    def _feed_no_data(self, data):
        line, data = data.split(b'\r\n',1)
        match = re.match(r"(.*) (.*) (.*)", line.decode())
        if(match is not None):
            self.methode = match.group(1)
            self.url = Url(match.group(2))
            self.protocol = match.group(3)
            self.state = STATE_HEADER
        else:
            raise Exception("Invalid Request",str(line))
        return data

    def _feed_request(self,data):
        line, data = data.split(b'\r\n',1)
        if len(line)==0:
            self.state = STATE_DATA
            self._check_header()
        else:
            match = re.match(r"(.*): (.*)", line.decode())
            if(match is not None):
                self.fields.append((match.group(1), match.group(2)))
            else:
                raise Exception("Invalid format field:", str(line))
        return data

    def _feed_data(self,data):
        if len(data) > self.data_length-len(self.data):
            self.data += data[:self.data_length-len(self.data)]
            self.state = STATE_COMPLET
            return data[self.data_length-len(self.data):]
        else:
            self.data += data
            return b''

    def _check_header(self):
        data_length = int(self.get_field("Content-Length", default='0'))
        if data_length == 0:
            self.state = STATE_COMPLET

    def completed(self):
        if self.state == STATE_COMPLET:
            return True
        return False

    def __str__(self):
        ret = str(self.methode)+" "+str(self.url)+" "+str(self.protocol)+"\r\n"
        for field in self.fields:
            ret += field[0]+": "+field[1]+"\r\n"
        ret += "\r\n"
        return ret

class Response(Http_proto):
    def __init__(self):
        Http_proto.__init__(self)
        self.proto = "HTTP/1.1"
        self.code = 404
        self.set_field("Server","Python-test/0.02")
        self.set_field("Content-length",'0')
        self.set_field("Content-type","text/text")

    def code_to_string(self,code):
        for el in http.HTTPStatus:
            if el.value == code:
                return el.phrase
        return ""

    def __str__(self):
        ret = self.proto+" "+str(self.code)+" "+self.code_to_string(self.code)+"\r\n"
        for field in self.fields:
            ret += field[0]+": "+str(field[1])+"\r\n"
        ret += "\r\n"
        return ret
