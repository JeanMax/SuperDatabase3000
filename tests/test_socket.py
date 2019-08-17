import superdatabase3000.socket as sckt

TEST_SOCK_FILENAME = "/tmp/superdatabase3000.test.sock"


def _on_msg(client_sock_fd, msg):
    print(client_sock_fd, msg)


def _on_yo(client_sock_fd, msg):
    assert "yo" == msg


def _on_big_yo(client_sock_fd, msg):
    assert "yo" * 42000 == msg


def test_socket():
    server = sckt.SocketServer(sock_filename=TEST_SOCK_FILENAME)
    client1 = sckt.SocketClient(sock_filename=TEST_SOCK_FILENAME)
    server.poll_events(_on_msg)
    fd1 = list(server.clients.keys())[0]
    client2 = sckt.SocketClient(sock_filename=TEST_SOCK_FILENAME)
    server.poll_events(_on_msg)
    fd2 = list(server.clients.keys())[1]
    if fd2 == fd1:
        fd2 = list(server.clients.values())[0]
    client1.send("yo")
    server.poll_events(_on_yo)
    client2.send("yo" * 42000)
    server.poll_events(_on_big_yo)
    server.send_to(server.clients[fd1].sock.fileno(), "hey")
    server.poll_events(_on_msg)
    server.send_to(server.clients[fd2].sock.fileno(), "ola")
    server.poll_events(_on_msg)
    assert client1.recv() == "hey"
    assert client2.recv() == "ola"
    del client1
    server.poll_events(_on_msg)
    del server
    del client2
