import os
import re
import time
import magic
import json

from pynet import http_tools
from pynet.network import Tcp_handler, Tcp_server_handler
from pythread.threadMananger import ThreadMananger, threadedFunction


def chunk(path, seek, size=1024*5):
    with open(path, "rb") as f:
        f.seek(seek)
        ret = f.read(size)
    return seek+len(ret), ret


def chunks(path, seek=-1, chunk_size=65500):
    with open(path, "rb") as f:
        if seek > 0:
            f.seek(seek)
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data

class HTTP_handler():
    def __init__(self, server, connection, request, args=[], kwargs=[]):
        self.request = request
        self.response = http_tools.HTTPResponse()
        self.connection = connection
        self.server = server
        self.dead = False
        if self.request.header.query == "GET":
            self.GET(self.request.header.url, *args, **kwargs)

        elif self.request.header.query == "PUT":
            self.PUT(self.request.header.url, *args, **kwargs)

        elif self.request.header.query == "DELETE":
            self.DELETE(self.request.header.url, *args, **kwargs)
        elif self.request.header.query == "POST":
            self.POST(self.request.header.url, *args, **kwargs)
        else:
            print("unknown method", self.request.header.query)

    def GET(self, url, *args, **kwargs):
        pass

    def PUT(self, url, *args, **kwargs):
        pass

    def DELETE(self, url, *args, **kwargs):
        pass

    def POST(self, url, *args, **kwargs):
        pass

    def send_text(self, code, data=None, content_type="text/text"):
        self.response.code = code
        if data is not None:
            self.response.fields.set("Content-Length", str(len(data)))
            self.response.fields.set("Content-type", content_type)
        else:
            data = ''
        self.connection.send(str(self.response).encode()+data.encode())

    def send_json(self, code, data={}):
        dump = json.dumps(data, sort_keys=True, indent=4)
        self.send_text(code, dump, content_type="application/json")

    def send_header(self, code):
        self.response.code = code
        self.connection.send(str(self.response).encode())

    def send_data(self, data):
        if type(data) is str:
            data = data.encode()
        return self.connection.send(data, chunk_size=0)

    def send_error(self, code):
        self.response.fields.set("Content-Length", str(0))
        self.send_header(code)
        self.send_data("")

    def send_file(self, path):
        r = self.request.header.fields.get("Range")
        self.response.fields.set("Content-type", magic.Magic(mime=True).from_file(path))
        seek = 0
        if r is not None:
            seek = int(r.split("=")[1][:-1])
        seek_end = os.path.getsize(path)-1  # seek end not fully implemented
        full_size = os.path.getsize(path)
        size = seek_end-seek+1

        if seek >= 0 and r is not None:
            self.response.fields.set("Accept-Ranges", "bytes")
            self.response.fields.set("Content-Range", "bytes "+str(seek)+"-"+str(seek_end)+"/"+str(full_size))
            self.response.fields.set("Content-length", size)
            self.send_header(206)
        else:
            self.response.fields.set("Accept-Ranges", "bytes")
            self.response.fields.set("Content-length", os.path.getsize(path))
            self.send_header(200)

        print(path, seek, seek_end, size)

        while True:
            seek, data = chunk(path, seek)
            while True:
                if self.connection.dead:
                    break
                if self.send_data(data):
                    break
                time.sleep(0.05)

            if seek >= full_size or self.connection.dead:
                print("end ", self.connection.dead)
                break


class HTTP_connection(Tcp_handler):

    def __init__(self, server):
        Tcp_handler.__init__(self, "HTTP_handler")
        self.current_Request = None
        self.server = server
        self.prev_data = b""
        self.dead = False

    def on_data(self, socket, data):
        if self.current_Request is None:
            self.current_Request = http_tools.HTTPRequest()
        self.prev_data = self.current_Request.feed(self.prev_data+data)
        if self.current_Request.completed():
            self.server.execute_request(self, self.current_Request)
            self.current_Request = None

    def on_close(self, socket):
        self.dead = True

    def close(self):
        self.dead = True


class HTTP_server(Tcp_server_handler, ThreadMananger):
    def __init__(self):
        Tcp_server_handler.__init__(self, HTTP_connection)
        ThreadMananger.__init__(self, nbr_thread=5)
        self.route = []

    @threadedFunction()
    def execute_request(self, socket_handler, request):
        handler, args, kwargs = self.get_route(request.header.url.path)
        if handler is not None:
            handler(self, socket_handler, request, args, kwargs)
        else:
            response = http_tools.HTTPResponse()
            response.code = 404
            response.fields.set("Content-Length", str(0))
            socket_handler.send(str(response).encode()+b"")
        request.close()

    def get_route(self, path):
        for regpath, handler, args, kwargs in self.route:
            m = re.fullmatch(regpath, path)
            if m is not None:
                for i in range(0, len(m.groups())):
                    args = list(args)
                    value = m.groups()[i]
                    if len(value) == 0:
                        value = None
                    args.insert(i, value)
                    args = tuple(args)
                return handler, args, kwargs
        return None, None, None

    def add_route(self, regpath, handler, *args, **kwargs):
        self.route.append((regpath, handler, args, kwargs))
