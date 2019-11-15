import base64
import hashlib
import struct

from pynet.http.tools import HTTP_CONNECTION_ABORT, HTTP_CONNECTION_UPGRADE

from pynet.http.handler import HTTPHandler
from pythread import threaded


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
    def __init__(self, request, room):
        self.request = request
        self.room = room
        self.room.new_client(self)

    def feed(self, data):
        message, data = webSocket_parse(data)
        self.room.exec_message(self, message)
        return data

    def send(self, fin, opcode, data):
        message = webSocket_compile(fin, opcode, data)
        self.request.connection.send(message, chunk_size=0)

    def send_text(self, text):
        self.send(1, 1, text.encode())

    def send_binary(self, binary):
        self.send(1, 2, binary)


class WebSocketRoom:
    def __init__(self, name=None):
        self.clients = []
        self.name = name

    @threaded("httpServer")
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
        elif message[1] == 8:
            self.clients.remove(client)
        elif message[1] == 1:
            self.on_message(client, message[2].decode())
        elif message[1] == 2:
            self.on_message(client, message[2])
        else:
            raise Exception("Opcode not implemented", message[1])

    def on_message(self, client, message):
        pass

    def on_new(self, client):
        pass

    def send(self, client, data):
        if client not in self.clients:
            raise Exception("client unknown")
        if type(data) == str:
            client.send_text(data)
        elif type(data) == bytearray:
            client.send_binary(data)
        else:
            raise Exception("Unknown type", type(data), data)

    def send_to_all(self, data):
        for client in self.clients:
            self.send(client, data)


class WebSocketEntryPoint(HTTPHandler):
    def prepare(self, headers):
        if not self.request.header.fields.get("Connection") == "Upgrade":
            return HTTP_CONNECTION_ABORT
        if not self.request.header.fields.get("Upgrade") == "websocket":
            return HTTP_CONNECTION_ABORT

        key = self.request.header.fields.get("Sec-WebSocket-Key")
        version = self.request.header.fields.get("Sec-WebSocket-Version")

        combined = key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        key_rep = base64.b64encode(hashlib.sha1(combined.encode()).digest())
        self.request.upgrade_client = WebSocketClient(self.request, self.user_data["ws_room"])

        self.response.fields.set("Upgrade", "websocket")
        self.response.fields.set("Connection", "Upgrade")
        self.response.fields.set("Sec-WebSocket-Accept", key_rep.decode())
        self.response.send_text(101, "")

        return HTTP_CONNECTION_UPGRADE
