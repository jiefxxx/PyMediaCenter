import sys
import traceback

from pynet.http.data import HTTPData
from pynet.http.tools import HTTP_CONNECTION_ABORT, HTTP_CONNECTION_CONTINUE

from pynet.http.response import HTTPResponse


class HTTPHandler:
    def __init__(self, request, args):
        self.user_data, self.request = args, request
        self.response = HTTPResponse(self.request)
        self.dead = False
        self.data = None

    def get_webSocket_room(self):
        return self.user_data.get("#ws_room")

    def prepare(self, header):
        content_length = int(header.fields.get("Content-Length", default='0'))
        if content_length > 0:
            self.data = HTTPData(content_length)
        return HTTP_CONNECTION_CONTINUE

    def feed(self, data_chunk):
        self.data.feed(data_chunk)

    def execute_request(self):
        try:
            self._execute_request()
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                                      file=sys.stdout)
            print(e)
            self.response.send_error(500)

    def _execute_request(self):
        if self.request.header.query == "GET":

            self.GET(self.request.header.url, *self.user_data["#regex_data"])

        elif self.request.header.query == "PUT":
            self.PUT(self.request.header.url, *self.user_data["#regex_data"])

        elif self.request.header.query == "DELETE":
            self.DELETE(self.request.header.url, *self.user_data["#regex_data"])

        elif self.request.header.query == "POST":
            self.POST(self.request.header.url, *self.user_data["#regex_data"])

        else:
            raise Exception("Unknown Method "+self.request.header.query)

    def GET(self, url, *args):
        self.response.send_error(404)

    def PUT(self, url, *args):
        self.response.send_error(404)

    def DELETE(self, url, *args):
        self.response.send_error(404)

    def POST(self, url, *args):
        self.response.send_error(404)

    def close(self):
        pass


class HTTP404Handler(HTTPHandler):
    def prepare(self, header):
        self.response.send_error(404)
        return HTTP_CONNECTION_ABORT


