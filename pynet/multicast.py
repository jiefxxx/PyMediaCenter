import socket
import struct
from asyncio import BaseProtocol


def init_multicastSock(mcast_group):
    multicastSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    multicastSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    multicastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
    #multicastSock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)
    multicastSock.bind(('', mcast_group[1]))
    group = socket.inet_aton(mcast_group[0])
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    multicastSock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return multicastSock


class EchoClientProtocol(BaseProtocol):
    def __init__(self, server_name, addr, callback):
        self.transport = None
        self.addr = addr
        self.callback = callback
        self.server_name = server_name

    def send_iam(self):
        if self.transport:
            self.transport.sendto(("IAM " + self.server_name).encode(), self.addr)

    def send_who(self):
        if self.transport:
            self.transport.sendto("WHO".encode(), self.addr)

    def connection_made(self, transport):
        self.transport = transport
        self.send_who()

    def datagram_received(self, data, addr):
        data = data.decode()
        if data[:3] == "WHO":
            self.send_iam()
        elif data[:3] == "IAM":
            if data[4:] != self.server_name:
                self.callback(data[4:], addr[0])

    def error_received(self, exc):
        print('Error received:', self, exc)

    def close(self):
        self.transport.close()


async def create_multicast_server(loop, server_name, callback, addr=('239.255.255.250', 10000)):
    transport, protocol = await  loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(server_name, addr, callback), sock=init_multicastSock(addr))
    return protocol
