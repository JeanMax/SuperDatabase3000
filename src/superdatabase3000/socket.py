"""TODO"""

import os
import socket
import select
import pickle
import collections

import superdatabase3000.packet as pckt


DEFAULT_SOCK_FILENAME = "/tmp/superdatabase3000.sock"
BUF_SIZE = 0x1000


def _send_to(sock, msg):
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


def _recv_from(sock):
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


def _msg_head_str(msg):
    """TODO"""
    msg_limit = 32
    msg_str = f"'{msg}'"
    if len(msg_str) > msg_limit:
        msg_str = msg_str[:msg_limit] + "'..."
    return msg_str


class _SocketBase():
    """TODO"""
    def __init__(self, sock_filename):
        """TODO"""
        if sock_filename is None:
            sock_filename = DEFAULT_SOCK_FILENAME
        self.sock_filename = sock_filename
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def __del__(self):
        """TODO"""
        self.sock.close()


class SocketClient(_SocketBase):
    """TODO"""

    def __init__(self, sock_filename=None):
        """TODO"""
        super().__init__(sock_filename)
        self._connect()

    def _connect(self):
        """TODO"""
        if not os.path.exists(self.sock_filename):
            raise socket.error(f"Can't find socket at '{self.sock_filename}'")
        self.sock.connect(self.sock_filename)

    def send(self, msg):
        """TODO"""
        _send_to(self.sock, msg)

    def recv(self):
        """TODO"""
        return _recv_from(self.sock)


Client = collections.namedtuple(
    "Client",
    ["sock", "to_send_msg_queue"]
)


class SocketServer(_SocketBase):
    """TODO"""
    # MAX_CLIENT = 64

    def __init__(self, sock_filename=None):
        """TODO"""
        super().__init__(sock_filename)
        self._listen()
        self.clients = {}  # dict(client_sock_fd: Client)

    def __del__(self):
        """TODO"""
        for client in self.clients.values():
            client.sock.close()
        super().__del__()

    def _listen(self):
        """TODO"""
        if os.path.exists(self.sock_filename):
            os.unlink(self.sock_filename)
        # self.sock.setblocking(0)
        self.sock.bind(self.sock_filename)
        self.sock.listen()

    def _accept(self):
        """TODO"""
        client_sock, _ = self.sock.accept()
        print("socket: accept:", client_sock)
        # client_sock.setblocking(0)
        self.clients[client_sock.fileno()] = Client(
            sock=client_sock,
            to_send_msg_queue=[]
        )

    def _remove_client(self, client_sock):
        """TODO"""
        print("socket: remove:", client_sock)
        fd = client_sock.fileno()
        client_sock.close()
        del self.clients[fd]

    def _handle_error_stream(self, sock):
        """TODO"""
        if sock is self.sock:
            print("socket: PANIC! error on server sock:", sock)
        else:
            print("socket: error on sock:", sock)
            self._remove_client(sock)

    def _handle_write_stream(self, sock):
        """TODO"""
        msg_queue = self.clients[sock.fileno()].to_send_msg_queue
        if msg_queue:
            msg = msg_queue.pop(0)
            print(
                f"socket: sending message {_msg_head_str(msg)} to sock: {sock}"
            )
            _send_to(sock, msg)

    def _handle_read_stream(self, sock, on_msg):
        """TODO"""
        if sock is self.sock:
            self._accept()
            return
        try:
            msg = _recv_from(sock)
        except ValueError:
            print("socket: received an empty/invalid packet, removing client")
            self._remove_client(sock)
            # TODO: do we really want to remove client sending invalid packets?
            return
        print(f"socket: received message: {_msg_head_str(msg)}")
        on_msg(sock.fileno(), msg)

    def poll_events(self, on_msg):
        """TODO"""
        inputs = [c.sock for c in self.clients.values()] + [self.sock]
        rlist, wlist, xlist = select.select(
            inputs,
            [c.sock for c in self.clients.values() if c.to_send_msg_queue],
            inputs,
            0.5
        )
        for sock in rlist:
            self._handle_read_stream(sock, on_msg)
        for sock in wlist:
            self._handle_write_stream(sock)
        for sock in xlist:
            self._handle_error_stream(sock)

    def send_to(self, client_sock_fd, msg):
        """TODO"""
        self.clients[client_sock_fd].to_send_msg_queue.append(msg)
