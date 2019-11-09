import queue
import select
import socket
import struct
import time

CHUNK_SIZE = 1024*5


def init_multicastSock(mcast_group, mcast_port):
    multicastSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    multicastSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    multicastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    multicastSock.bind(('', mcast_port))
    group = socket.inet_aton(mcast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    multicastSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return multicastSock


def init_serverSock(port, listen=10):
    serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSock.bind(('', port))
    serverSock.listen(listen)
    return serverSock


class Handler:
    def __init__(self, name, chunk_size=CHUNK_SIZE):
        self.send_queue = queue.Queue(maxsize=10)
        self.chunk_size = chunk_size
        self.name = name
        self.addr = None

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

    def on_init(self, mainServer, socket):
        self.mainServer = mainServer
        print("init socket(" + self.name + ") :" + str(self.addr))

    def on_exceptional(self, socket):
        print("close socket(" + self.name + ") :" + str(self.addr))

    def on_readable(self, socket):
        pass

    def on_writable(self, socket):
        pass


class Tcp_server_handler(Handler):

    def __init__(self, client_handler):
        Handler.__init__(self, "server")
        self.client_handler = client_handler

    def on_init(self, mainServer, sock):
        self.addr = sock.getsockname()
        Handler.on_init(self, mainServer, sock)

    def on_readable(self, sock):
        s, addr = sock.accept()
        #s.settimeout(0.5)
        self.mainServer.add_socket(s, self.client_handler(self))


class Tcp_handler(Handler):

    def on_init(self, mainServer, sock):
        self.addr = sock.getpeername()
        Handler.on_init(self, mainServer, sock)

    def on_readable(self, sock):
        try:
            data = sock.recv(self.chunk_size)
            if len(data) > 0:
                self.on_data(sock, data)
            else:
                self.on_exceptional(sock)
                self.on_close(sock)
                self.mainServer.remove_socket(sock)
                sock.close()
        except ConnectionResetError:
            self.on_exceptional(sock)
            self.on_close(sock)
            self.mainServer.remove_socket(sock)
            sock.close()

    def on_writable(self, sock):
        if not self.send_queue.empty():
            data = self.send_queue.get()
            try:
                # print("send :", len(data))
                sock.send(data)
            except socket.error:
                print("error socket(" + self.name + ") :" + str(self.addr))
                # print(sock.getpeername())
                # print(data)
                self.dead = True
        elif self.dead:
            self.on_close(sock)
            self.mainServer.remove_socket(sock)
            sock.close()

    def on_data(self, sock, data):
        print(data)
        pass

    def on_close(self, sock):
        # print("close")
        pass


class MainServer():
    def __init__(self, chunk_size=1024):
        self.socket_map = {}

    def add_socket(self, socket, handler):
        handler.on_init(self, socket)
        self.socket_map[socket] = handler

    def get_handler(self, socket):
        return self.socket_map[socket]

    def get_sockets(self):
        return list(self.socket_map.keys())

    def remove_socket(self, socket):
        del (self.socket_map[socket])

    def close(self):
        for sock in self.get_sockets():
            self.get_handler(sock).close()
            self.remove_socket(sock)
            sock.close()

    def run_once(self):
        socks = self.get_sockets()
        # print(socks)
        readable, writable, exceptional = select.select(socks, socks, socks, 0)

        void = True
        for s in exceptional:
            self.get_handler(s).on_exceptional(s)
            self.remove_socket(s)
            void = False

        for s in writable:
            self.get_handler(s).on_writable(s)
            void = False

        for s in readable:
            self.get_handler(s).on_readable(s)
            void = False

        if void:
            time.sleep(0.05)
