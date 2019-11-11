from pynet.http.header import HTTPHeader


class HTTPRequest:
    def __init__(self, connection):
        self.connection = connection
        self.header = HTTPHeader()
        self.data_count = None
        self.handler = None
        self.header_completed = False
        self.prepare_return = -1
        self.upgrade_client = None

    def upgrade(self, client):
        self.upgrade_client = client

    def feed(self, data):
        while b'\r\n' in data and not self.header_completed:
            line, data = data.split(b'\r\n', 1)
            if len(line) == 0:
                self.header_completed = True
                handler, args = self.connection.server.get_route(self.header.url.path)
                self.handler = handler(self.header, self.connection, args)
                self.data_count = int(self.header.fields.get("Content-Length", default='0'))
                self.prepare_return = self.handler.prepare(self.header)
            else:
                self.header.parse_line(line)

        if self.header_completed and self.data_count > 0:
            if len(data) > self.data_count:
                self.data_count -= len(data[:self.data_count])
                self.handler.feed(data[:self.data_count])
                data = data[self.data_count:]
            else:
                self.data_count -= len(data)
                self.handler.feed(data)
                data = b""

        return data

    def completed(self):
        if self.data_count is None:
            return False
        if self.header_completed and self.data_count == 0:
            return True
        elif self.data_count < 0:
            raise Exception("Error in data count "+str(self.data_count))
        return False

    def close(self):
        self.connection.finished()
        if self.handler:
            self.handler.close()
