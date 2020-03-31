"""This module create an client/server interface over an unix socket."""

import os
import socket
import select
import pickle
import collections

import superdatabase3000.packet as pckt


DEFAULT_SOCK_FILENAME = "/tmp/superdatabase3000.sock"
BUF_SIZE = int(os.environ.get("BUF_SIZE_3000", 0x8000))
# if you experience broken pipe errors, you might want to change this


def _send_to(sock, msg):
    """
    Send 'msg' to given 'sock'.

    'msg' can be any python object, it will be pickled first, then sent
    as a packet to the socket.
    """
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
    """
    Receive a message from the given 'sock'.

    The returned message can be any valid python object.
    This function will block till a packet is fully received.
    """
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
    """A utility to print the head of the str representation of an object."""
    msg_limit = 32
    msg_str = f"'{msg}'"
    if len(msg_str) > msg_limit:
        msg_str = msg_str[:msg_limit] + "'..."
    return msg_str


class _SocketBase():
    """Base socket class for client/server socket."""

    def __init__(self, sock_filename):
        """Open a unix socket on the given 'sock_filename' path."""
        if sock_filename is None:
            sock_filename = DEFAULT_SOCK_FILENAME
        self.sock_filename = sock_filename
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def __del__(self):
        """Close the previously opened socket."""
        self.sock.close()


class SocketClient(_SocketBase):
    """
    This class can exchange messages with a SocketServer over a unix socket.
    """

    def __init__(self, sock_filename=None):
        """
        Initialize the connection to the SocketServer on the given
        'sock_filename' unix socket path.
        """
        super().__init__(sock_filename)
        self._connect()

    def _connect(self):
        """
        Connect to the SocketServer on 'self.sock_filename'.

        This function might raise a socket.error if it fails to connect.
        """
        if not os.path.exists(self.sock_filename):
            raise socket.error(f"Can't find socket at '{self.sock_filename}'")
        self.sock.connect(self.sock_filename)

    def send(self, msg):
        """Send a 'msg' (any python object) to the SocketServer."""
        _send_to(self.sock, msg)

    def recv(self):
        """Receive a message (any python object) from the SocketServer."""
        return _recv_from(self.sock)


# This named-tuple is used to represent a client from the server perspective
_Client = collections.namedtuple(
    "_Client",
    ["sock", "to_send_msg_queue"]
)


class SocketServer(_SocketBase):
    """
    This class can exchange messages with multiples clients over a unix socket.
    """

    def __init__(self, sock_filename=None):
        """
        Start listening for SocketClient on the given
        'sock_filename' unix socket path.
        """
        super().__init__(sock_filename)
        self._listen()
        self.clients = {}  # dict(client_sock_fd: _Client)

    def __del__(self):
        """Ensure each connection is closed."""
        for client in self.clients.values():
            client.sock.close()
        super().__del__()

    def _listen(self):
        """Listen for SocketClient on 'self.sock_filename'."""
        if os.path.exists(self.sock_filename):
            os.unlink(self.sock_filename)
        # self.sock.setblocking(0)
        self.sock.bind(self.sock_filename)
        self.sock.listen()

    def _accept(self):
        """Accept a new SocketClient."""
        client_sock, _ = self.sock.accept()
        print("socket: accept:", client_sock)
        # client_sock.setblocking(0)
        self.clients[client_sock.fileno()] = _Client(
            sock=client_sock,
            to_send_msg_queue=[]
        )

    def _remove_client(self, client_sock):
        """Remove a SocketClient."""
        print("socket: remove:", client_sock)
        fd = client_sock.fileno()
        client_sock.close()
        del self.clients[fd]

    def _handle_error_stream(self, sock):
        """Handle socket 'sock' with an error status returned by select."""
        if sock is self.sock:
            print("socket: PANIC! error on server sock:", sock)
            # it's the server socket itself, so we're screwed anyway :/
        else:
            print("socket: error on sock:", sock)
            self._remove_client(sock)

    def _handle_write_stream(self, sock):
        """Handle socket 'sock' which can be written to."""
        msg_queue = self.clients[sock.fileno()].to_send_msg_queue
        if not msg_queue:
            return
        msg = msg_queue.pop(0)
        print(f"socket: sending message {_msg_head_str(msg)} to sock: {sock}")
        _send_to(sock, msg)

    def _handle_read_stream(self, sock, on_msg):
        """
        Handle socket 'sock' which can be read from.

        """
        if sock is self.sock:
            self._accept()
            return
        try:
            msg = _recv_from(sock)
        except ValueError:
            print("socket: received an empty/invalid packet, removing client")
            self._remove_client(sock)
            return
        print(f"socket: received message: {_msg_head_str(msg)}")
        on_msg(sock.fileno(), msg)

    def poll_events(self, on_msg, timeout=0.5):
        """
        Check for events on the server.

        This will handle:
        - accepting/removing clients
        - sending messages (the ones added to the queue with send_to)
        - reading messages

        If a message is successfully read from the socket, the 'on_msg' callback
        will be called with 2 parameters: on_msg(socket_fd, msg)
        - socket_fd (int):  the socket fd of the client
        - msg (object):     the message received from the client
        (You can use 'socket_fd' to answer to the client with send_to)
        """
        inputs = [c.sock for c in self.clients.values()] + [self.sock]
        rlist, wlist, xlist = select.select(
            inputs,
            [c.sock for c in self.clients.values() if c.to_send_msg_queue],
            inputs,
            timeout
        )
        for sock in rlist:
            if sock.fileno() >= 0:
                self._handle_read_stream(sock, on_msg)
        for sock in wlist:
            if sock.fileno() >= 0:
                self._handle_write_stream(sock)
        for sock in xlist:
            self._handle_error_stream(sock)

    def send_to(self, client_sock_fd, msg):
        """
        Send a message 'msg' (any python object)
        to the socket fd 'client_sock_fd'.

        Actually it will just put the message in a queue, eh. The message will
        be sent on a later call to poll_events if the socket destination can
        be written to.
        """
        self.clients[client_sock_fd].to_send_msg_queue.append(msg)
