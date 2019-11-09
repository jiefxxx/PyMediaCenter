from pynet.http_data import HTTPData
from pynet.http_response import HTTPResponse
from pynet.http_tools import HTTP_CONNECTION_ABORT, HTTP_CONNECTION_CONTINUE


class HTTPHandler:
    def __init__(self, request, args):
        self.user_data, self.request = args, request
        self.response = HTTPResponse(self.request)
        self.dead = False
        self.data = None

    def prepare(self, header):
        content_length = int(header.fields.get("Content-Length", default='0'))
        if content_length > 0:
            self.data = HTTPData(content_length)
        return HTTP_CONNECTION_CONTINUE

    def feed(self, data_chunk):
        self.data.feed(data_chunk)

    def execute_request(self):

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


class HTTP404(HTTPHandler):
    def prepare(self, header):
        self.response.send_error(404)
        return HTTP_CONNECTION_ABORT


