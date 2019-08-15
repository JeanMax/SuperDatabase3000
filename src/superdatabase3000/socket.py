"""TODO"""

import os
import socket
import select
import pickle
import collections

import superdatabase3000.packet as pckt


DEFAULT_SOCK_FILENAME = "/tmp/superdatabase3000.sock"
BUF_SIZE = 0x1000


def send_to(sock, msg):
    """TODO"""
    payload = pickle.dumps(msg)
    bytes_buf = pckt.pack(payload)
    del payload

    sock.send(bytes_buf[:pckt.PACKET_MIN_SIZE])
    bytes_buf = bytes_buf[pckt.PACKET_MIN_SIZE:]
    while bytes_buf:
        buf_size = min(len(bytes_buf), BUF_SIZE)
        sock.send(bytes_buf[:buf_size])
        bytes_buf = bytes_buf[buf_size:]


def recv_from(sock):
    """TODO"""
    bytes_buf = sock.recv(pckt.PACKET_MIN_SIZE)
    packet = pckt.unpack(bytes_buf)

    if packet.payload_size != len(packet.payload):
        bytes_to_read = packet.payload_size - len(packet.payload)
        while bytes_to_read:
            buf_size = min(bytes_to_read, BUF_SIZE)
            bytes_buf += sock.recv(buf_size)
            bytes_to_read -= buf_size
        packet = pckt.unpack(bytes_buf)

    msg = pickle.loads(packet.payload)
    return msg


class SocketClient():
    """TODO"""

    def __init__(self, sock_filename=DEFAULT_SOCK_FILENAME):
        """TODO"""
        self.sock_filename = sock_filename
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.connect()

    def __del__(self):
        """TODO"""
        self.sock.close()

    def connect(self):
        """TODO"""
        if not os.path.exists(self.sock_filename):
            raise socket.error(f"Can't find socket at '{self.sock_filename}'")
        self.sock.connect(self.sock_filename)

    def send(self, msg):
        """TODO"""
        send_to(self.sock, msg)

    def recv(self):
        """TODO"""
        return recv_from(self.sock)


Client = collections.namedtuple(
    "Client",
    ["sock", "read_msg_queue", "to_send_msg_queue"]
)


class SocketServer():
    """TODO"""
    # MAX_CLIENT = 64

    def __init__(self, sock_filename=DEFAULT_SOCK_FILENAME):
        """TODO"""
        self.sock_filename = sock_filename
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.listen()
        self.clients = {}  # dict(client_sock_fd: Client)

    def __del__(self):
        """TODO"""
        for client in self.clients.values():
            client.sock.close()
        self.sock.close()

    def listen(self):
        """TODO"""
        if os.path.exists(self.sock_filename):
            os.unlink(self.sock_filename)
        self.sock.setblocking(0)
        self.sock.bind(self.sock_filename)
        self.sock.listen()

    def accept(self):
        """TODO"""
        client_sock, _ = self.sock.accept()
        print("ACCEPT:", client_sock) # DEBUG
        # client_sock.setblocking(0)
        self.clients[client_sock.fileno()] = Client(
            sock=client_sock,
            read_msg_queue=[],
            to_send_msg_queue=[]
        )

    def remove_client(self, client_sock):
        """TODO"""
        print("REMOVE:", client_sock) # DEBUG
        fd = client_sock.fileno()
        client_sock.close()
        del self.clients[fd]

    def send_to(self, client_sock, msg):
        """TODO"""
        self.clients[client_sock.fileno()].to_send_msg_queue.append(msg)

    def select(self):
        """TODO"""
        inputs = [c.sock for c in self.clients.values()] + [self.sock]
        rlist, wlist, xlist = select.select(
            inputs,
            [c.sock for c in self.clients.values() if c.to_send_msg_queue],
            inputs,
            0
        )
        for sock in rlist:
            self.handle_read_stream(sock)
        for sock in wlist:
            self.handle_write_stream(sock)
        for sock in xlist:
            self.handle_error_stream(sock)

    def handle_read_stream(self, sock):
        """TODO"""
        if sock is self.sock:
            print("new client on", sock) # DEBUG
            self.accept()
            return
        print("can read from", sock) # DEBUG
        try:
            msg = recv_from(sock)
        except ValueError:
            print("no msg / not a packet, removing", sock) # DEBUG
            self.remove_client(sock)
            return
        print("msg:", msg) # DEBUG
        self.clients[sock.fileno()].read_msg_queue.append(msg)

    def handle_write_stream(self, sock):
        """TODO"""
        print("can write to", sock) # DEBUG
        msg_queue = self.clients[sock.fileno()].to_send_msg_queue
        if msg_queue:
            msg = msg_queue.pop(0)
            send_to(sock, msg)

    def handle_error_stream(self, sock):
        """TODO"""
        if sock is self.sock:
            print("PANIC! error on", sock) # DEBUG
        else:
            print("error on", sock) # DEBUG
            self.remove_client(sock)
