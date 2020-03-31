"""
This is the main module of superdatabase3000.

You'll find here the client/server classes.
"""

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


def append_doc_of(fun):
    """A decorator to append the documentation of a function to another."""
    def decorator(this_fun):
        this_fun.__doc__ += fun.__doc__
        return this_fun

    return decorator


class DbClient():
    """A client to interact with your favorite database."""

    def __init__(self, sock_filename=None):
        """
        Parameters
        ----------
        sock_filename : str
        path to the DbServer socket

        Examples
        --------
        # assuming a server is already launched
        client = DbClient("/tmp/db.sock")
        df = client.select("/toto")
        """
        self.socket = SocketClient(sock_filename)

    def __del__(self):
        """Close the socket."""
        del self.socket

    def _query(self, method, args):
        """Send a query to the server."""
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

    @append_doc_of(HdfStoreManager.select)
    def select(self, table, where=None, columns=None, start=None, stop=None):
        """This method is an interface to the hdf object on the server side."""
        return self._query("select", Args(table, where, columns, start, stop))

    @append_doc_of(HdfStoreManager.insert)
    def insert(self, table, df):
        """This method is an interface to the hdf object on the server side."""
        return self._query("insert", Args(table, df=df))

    @append_doc_of(HdfStoreManager.delete)
    def delete(self, table, where):
        """This method is an interface to the hdf object on the server side."""
        return self._query("delete", Args(table, where))

    @append_doc_of(HdfStoreManager.drop)
    def drop(self, table):
        """This method is an interface to the hdf object on the server side."""
        return self._query("drop", Args(table))


class DbServer():
    """A server running your favorite database."""

    def __init__(self, sock_filename=None, hdf_filename=None):
        """
        Parameters
        ----------
        sock_filename : str
        path to the DbServer socket

        hdf_filename : str
        path to the DbServer socket

        Examples
        --------
        server = DbServer(
            sock_filename="/tmp/db.sock",
            hdf_filename="/tmp/db.h5"
        )
        server.read_loop()
        """
        self.socket = SocketServer(sock_filename)
        self.hdf = HdfStoreManager(hdf_filename)
        self.sig = ExitSignalWatcher()
        self.sig.catch()
        self.hdf.maintain()  # TODO: not sure when to do this

    @append_doc_of(SocketServer.poll_events)
    def read_loop(self):
        """Poll events in an infinite loop."""
        while not self.sig.EXIT:
            self.socket.poll_events(self._on_msg)
        exit_code = self.sig.EXIT
        self.__del__()
        sys.exit(exit_code)

    def _on_msg(self, client_sock_fd, msg):
        """Callback to send hdf query result to the client."""
        hdf_method = self.hdf.__class__.__dict__[msg["method"]]
        query = hdf_method(self.hdf, **msg["args"])
        self.socket.send_to(client_sock_fd, query)
        if msg["method"] != "select":  # insert/delete/drop
            self.hdf.flush()

    def __del__(self):
        """Close what needs to be."""
        if getattr(self, "hdf", None) is not None:
            del self.hdf
        if getattr(self, "socket", None) is not None:
            del self.socket
        if getattr(self, "sig", None) is not None:
            self.sig.restore()
            del self.sig
