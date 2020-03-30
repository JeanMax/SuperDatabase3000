import time
import signal
import os
import numpy as np
import pandas as pd
import pytest

import superdatabase3000.superdatabase3000 as db

SOCK = "/tmp/db3000.sock"
HDF = "/tmp/db3000.hdf"

DF = pd.DataFrame(np.random.random((10000, 12)))


def client_side():
    time.sleep(0.3)  # wait for server
    client1 = db.DbClient(sock_filename=SOCK)  # 1
    client2 = db.DbClient(sock_filename=SOCK)  # 2

    client1.insert("/tata", DF)  # 4
    # 4

    df = client2.select("/tata")  # 6
    assert not len((df == DF).replace(True, np.nan).dropna())

    client1.insert("/toto", DF)  # 8
    client1.delete("/toto", where="index > 42")  # 10
    client2.drop("/toto")  # 12
    del client1  # 13
    del client2  # 14


def server_side():
    if os.path.exists(HDF):
        os.unlink(HDF)
    server = db.DbServer(sock_filename=SOCK, hdf_filename=HDF)
    for _ in range(14):
        server.socket.poll_events(server._on_msg)
    del server


@pytest.mark.filterwarnings("ignore:numpy.ufunc size changed")
def test_db():
    child_pid = os.fork()
    if not child_pid:
        client_side()
        return
    else:
        server_side()

    child_pid = os.fork()
    if not child_pid:
        server_side()
        return
    else:
        client_side()
        time.sleep(0.3)
        os.kill(child_pid, signal.SIGINT)
