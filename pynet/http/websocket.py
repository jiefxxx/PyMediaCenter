import base64
import hashlib
import json
import struct

from pynet.http.tools import HTTP_CONNECTION_ABORT, HTTP_CONNECTION_UPGRADE

from pynet.http.handler import HTTPHandler
from pythread import threaded


def webSocket_process_key(key):
    combined = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    return base64.b64encode(hashlib.sha1(combined.encode()).digest())


def webSocket_parse(data):
    opcode, data = int.from_bytes(data[:1], byteorder='big'), data[1:]
    fin = (int(0xF0) & opcode) >> 7
    opcode = int(0x0F) & opcode

    size, data = int.from_bytes(data[:1], byteorder='big'), data[1:]
    mask_b = size >> 7
    size -= 128
    if size == 126:
        b_size, data = data[:2], data[2:]
        size = int.from_bytes(b_size, byteorder='big')
    elif size == 127:
        b_size, data = data[:8], data[8:]
        size = int.from_bytes(b_size, byteorder='big')

    mask = b""
    if mask_b == 1:
        mask, data = data[:4], data[4:]

    raw_data, data = data[:size], data[size:]
    if mask_b == 1:
        message_data = bytearray()
        for i in range(0, len(raw_data)):
            message_data.append(raw_data[i] ^ mask[i % 4])
        message_data = bytes(message_data)
    else:
        message_data = raw_data

    return (fin, opcode, message_data), data


def webSocket_compile(fin, opcode, data):
    send_message = bytearray()
    send_data = bytearray(data)
    mask_b = 0

    _opcode = opcode | (fin << 7)
    send_message.append(_opcode)

    size = len(send_data)
    if 125 < size <= 0xFFFF:
        _size = 126 | mask_b << 7
        send_message.append(_size)
        send_message += struct.pack(">H", size)
    elif size > 0xFFff:
        _size = 127 | mask_b << 7
        send_message.append(_size)
        send_message += struct.pack(">Q", size)
    else:
        _size = size | mask_b << 7
        send_message.append(_size)

    send_message += send_data

    return send_message


class WebSocketClient:
    def __init__(self, header, connection, room):
        self.request_header = header
        self.connection = connection
        self.room = room
        self.room.new_client(self)

    def error(self):
        self.room.on_error(self)

    def feed(self, data):
        message, data = webSocket_parse(data)
        self.room.exec_message(self, message)
        return data

    def send(self, fin, opcode, data):
        message = webSocket_compile(fin, opcode, data)
        self.connection.send(message, chunk_size=0)

    def send_text(self, text):
        self.send(1, 1, text.encode())

    def send_binary(self, binary):
        self.send(1, 2, binary)

    def ping(self):
        self.send(1, 0x09, b"42")


class WebSocketRoom:
    def __init__(self, name=None):
        self.clients = []
        self.name = name

    def new_client(self, client):
        if client not in self.clients:
            self.clients.append(client)
            self.on_new(client)

    @threaded("httpServer")
    def exec_message(self, client, message):
        if client not in self.clients:
            raise Exception("client unknown")
        if message[1] == 9:
            client.send((1, 10, message[2]))
        elif message[1] == 0x0A:
            pass
        elif message[1] == 8:
            self.on_close(client)
            self.clients.remove(client)
        elif message[1] == 1:
            self.on_message(client, message[2].decode())
        elif message[1] == 2:
            self.on_message(client, message[2])
        else:
            raise Exception("Opcode not implemented", message[1])

    @threaded("httpServer")
    def on_error(self, client):
        self.on_close(client)
        self.clients.remove(client)

    def on_message(self, client, message):
        pass

    def on_new(self, client):
        pass

    def on_close(self, client):
        pass

    def send(self, data, client=None):
        if client is None:
            for client in self.clients:
                self.send(data, client=client)
        elif client not in self.clients:
            raise Exception("client unknown")
        elif type(data) == str:
            client.send_text(data)
        elif type(data) == bytearray:
            client.send_binary(data)
        else:
            raise Exception("Unknown type", type(data), data)

    def ping_all(self):
        for client in self.clients:
            client.ping()

    def send_json(self, data, client=None):
        data = json.dumps(data, sort_keys=True, indent=4)
        self.send(data, client=client)


class WebSocketEntryPoint(HTTPHandler):
    def prepare(self):
        key = self.header.get_webSocket_upgrade()
        room = self.get_webSocket_room()
        if key or room is None:
            print(key, room)
            return HTTP_CONNECTION_ABORT

        key = webSocket_process_key(key)

        self.upgrade(WebSocketClient(self.header, self.connection, room))

        return self.response.upgrade_webSocket(key)
