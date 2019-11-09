import re

import pynet.http_request
import pynet.http_response
from pynet.http_handler import HTTP404
from pynet.http_tools import HTTP_CONNECTION_ABORT, HTTP_CONNECTION_CONTINUE, HTTP_CONNECTION_UPGRADE
from pynet.network import Tcp_handler, Tcp_server_handler
from pythread.threadMananger import ThreadMananger, threadedFunction


class HTTPConnection(Tcp_handler):

    def __init__(self, server):
        Tcp_handler.__init__(self, "HTTP_handler")
        self.current_Request = None
        self.server = server
        self.prev_data = b""
        self.dead = False
        self.upgrade_client = None

    def on_data(self, socket, data):
        if self.upgrade_client:
            self.prev_data = self.upgrade_client.feed(self.prev_data + data)
            return

        if self.current_Request is None:
            self.current_Request = pynet.http_request.HTTPRequest(self)
        self.prev_data = self.current_Request.feed(self.prev_data + data)

        if self.current_Request.completed():
            if self.current_Request.prepare_return == HTTP_CONNECTION_ABORT:
                self.close()
                return
            if self.current_Request.prepare_return == HTTP_CONNECTION_CONTINUE:
                self.server.execute_request(self.current_Request)
                self.current_Request = None
                return
            if self.current_Request.prepare_return == HTTP_CONNECTION_UPGRADE:
                self.upgrade_client = self.current_Request.upgrade_client
                return

    def on_close(self, socket):
        self.dead = True

    def close(self):
        self.dead = True


class HTTPServer(Tcp_server_handler, ThreadMananger):
    def __init__(self):
        Tcp_server_handler.__init__(self, HTTPConnection)
        ThreadMananger.__init__(self, nbr_thread=5)
        self.route = []
        self.user_data = {}

    @threadedFunction()
    def execute_request(self, request):
        request.handler.execute_request()
        request.close()

    def get_route(self, path):
        for reg_path, handler, user_data in self.route:
            m = re.fullmatch(reg_path, path)
            if m is not None:
                user_data.update(self.user_data)
                args = []
                for group in m.groups():
                    if len(group) == 0:
                        group = None
                    args.append(group)
                user_data["#regex_data"] = tuple(args)
                return handler, user_data
        return HTTP404, {"#regex_data": ()}

    def add_user_data(self, name, value):
        self.user_data[name] = value

    def add_route(self, reg_path, handler, user_data=None, ws=None):
        if not user_data:
            user_data = {}
        if ws is not None:
            user_data["ws_room"] = ws
        self.route.append((reg_path, handler, user_data))
