import queue
import select
import socket
import struct

CHUNK_SIZE = 1024*5


def init_multicastSock(mcast_group, mcast_port):
    multicast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    multicast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicast_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    multicast_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    multicast_sock.bind(('', mcast_port))
    group = socket.inet_aton(mcast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    multicast_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return multicast_sock


def init_serverSock(port, listen=10):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('', port))
    server_sock.listen(listen)
    return server_sock


class Handler:
    def __init__(self, name, chunk_size=CHUNK_SIZE):
        self.send_queue = queue.Queue(maxsize=100)
        self.chunk_size = chunk_size
        self.name = name
        self.addr = None
        self.main_server = None
        self.terminated = False
        self.finish = False

    def send(self, data, chunk_size=None):
        if chunk_size is None:
            chunk_size = self.chunk_size
        if chunk_size > 0:
            while len(data) > chunk_size:
                self.send_queue.put(data[:chunk_size])
                data = data[chunk_size:]
            self.send_queue.put(data)
        else:
            if not self.send_queue.full():
                self.send_queue.put(data)
                return True
            else:
                return False

    def on_init(self, main_server, sock):
        self.main_server = main_server
        print("init socket(" + self.name + ") :" + str(self.addr))

    def on_close(self, sock):
        print("close socket(" + self.name + ") :" + str(self.addr))

    def on_readable(self, sock):
        pass

    def on_writable(self, sock):
        pass

    def readable(self):
        return False

    def finished(self):
        self.finish = True

    def kill(self):
        self.terminated = True

    def is_alive(self):
        return not self.terminated

    def close(self):
        pass


class TcpServerHandler(Handler):

    def __init__(self, client_handler):
        Handler.__init__(self, "server")
        self.client_handler = client_handler

    def on_init(self, main_server, sock):
        self.addr = sock.getsockname()
        Handler.on_init(self, main_server, sock)

    def on_readable(self, sock):
        s, addr = sock.accept()
        self.main_server.add_socket(s, self.client_handler(self))


class TcpHandler(Handler):

    def on_init(self, main_server, sock):
        self.addr = sock.getpeername()
        Handler.on_init(self, main_server, sock)

    def on_readable(self, sock):
        try:
            data = sock.recv(self.chunk_size)
            if len(data) > 0:
                self.on_data(data)
            else:
                self.kill()
        except ConnectionResetError:
            self.kill()

    def on_writable(self, sock):
        data = self.send_queue.get()
        try:
            sock.send(data)
        except socket.error:
            self.kill()

    def readable(self):
        return not self.send_queue.empty()

    def on_data(self, data):
        pass


class MainServer:
    def __init__(self):
        self.socket_map = {}

    def add_socket(self, sock, handler):
        handler.on_init(self, sock)
        self.socket_map[sock] = handler

    def get_handler(self, sock):
        return self.socket_map[sock]

    def get_sockets(self):
        readable = []
        writeable = []
        for sock in list(self.socket_map.keys()):

            if self.socket_map[sock].terminated:
                self.remove_socket(sock)
            elif self.socket_map[sock].readable():
                readable.append(sock)
                writeable.append(sock)
            elif self.socket_map[sock].finish:
                self.remove_socket(sock)
            else:
                readable.append(sock)

        return readable, writeable

    def remove_socket(self, sock):
        handler = self.get_handler(sock)
        handler.kill()
        handler.on_close(sock)
        handler.close()
        del (self.socket_map[sock])
        sock.close()

    def close(self):
        for sock in list(self.socket_map.keys()):
            self.remove_socket(sock)

    def run_once(self):
        input_sock, output_sock = self.get_sockets()
        readable, writable, exceptional = select.select(input_sock, output_sock, input_sock, 0.01)

        for s in exceptional:
            self.get_handler(s).on_exceptional(s)
            self.remove_socket(s)

        for s in writable:
            self.get_handler(s).on_writable(s)

        for s in readable:
            self.get_handler(s).on_readable(s)
