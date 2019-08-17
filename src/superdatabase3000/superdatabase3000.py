"""TODO"""

import sys
import collections

from superdatabase3000.signal import ExitSignalWatcher
from superdatabase3000.socket import SocketClient, SocketServer
from superdatabase3000.hdf import HdfStoreManager


Args = collections.namedtuple(
    "Args",
    ["table", "where", "columns", "start", "stop", "df"],
    # defaults=[None, None, None, None, None, None]  # >=3.7
)
Args.__new__.__defaults__ = (None,) * len(Args._fields)


class DbClient():
    """
blabla
    """

    def __init__(self, sock_filename=None):
        """
blabla

Parameters
----------
arg : type
    blabla

Examples
--------
blabla
        """
        self.socket = SocketClient(sock_filename)

    def __del__(self):
        """TODO"""
        del self.socket

    def _query(self, method, args):
        """TODO"""
        args_dic = args._asdict()
        if args_dic["table"][0] != "/":
            args_dic["table"] = "/" + args_dic["table"]
        self.socket.send({
            "method": method,
            "args": {
                k: args_dic[k]
                for k in args_dic
                if args_dic[k] is not None
            }
        })
        return self.socket.recv()

    def select(self, table, where=None, columns=None, start=None, stop=None):
        """TODO"""
        return self._query("select", Args(table, where, columns, start, stop))

    def insert(self, table, df):
        """TODO"""
        return self._query("insert", Args(table, df=df))

    def delete(self, table, where):
        """TODO"""
        return self._query("delete", Args(table, where))

    def drop(self, table):
        """TODO"""
        return self._query("drop", Args(table))


class DbServer():
    """
blabla
    """

    def __init__(self, sock_filename=None, hdf_filename=None):
        """
blabla

Parameters
----------
arg : type
    blabla

Examples
--------
blabla
        """
        self.socket = SocketServer(sock_filename)
        self.hdf = HdfStoreManager(hdf_filename)
        self.sig = ExitSignalWatcher()
        self.sig.catch()

    def read_loop(self):
        """TODO"""
        while not self.sig.EXIT:
            self.socket.poll_events(self._on_msg)
        self.__del__()
        sys.exit(self.sig.EXIT)

    def _on_msg(self, client_sock_fd, msg):
        """TODO"""
        hdf_method = self.hdf.__class__.__dict__[msg["method"]]
        query = hdf_method(self.hdf, **msg["args"])
        self.socket.send_to(client_sock_fd, query)
        if msg["method"] != "select":  # insert/delete/drop
            self.hdf.flush()

    def __del__(self):
        """TODO"""
        self.hdf.flush()
        self.hdf.maintain()
        del self.hdf
        del self.socket
        self.sig.restore()
