import superdatabase3000.socket as sckt

TEST_SOCK_FILENAME = "/tmp/superdatabase3000.test.sock"


def test_socket():
    server = sckt.SocketServer(sock_filename=TEST_SOCK_FILENAME)
    client1 = sckt.SocketClient(sock_filename=TEST_SOCK_FILENAME)
    server.select()
    fd1 = list(server.clients.keys())[0]
    client2 = sckt.SocketClient(sock_filename=TEST_SOCK_FILENAME)
    server.select()
    fd2 = list(server.clients.keys())[1]
    if fd2 == fd1:
        fd2 = list(server.clients.values())[0]
    client1.send("yo")
    server.select()
    client2.send("yo" * 42000)
    server.select()
    assert server.clients[fd1].read_msg_queue[0] == "yo"
    assert server.clients[fd2].read_msg_queue[0] == "yo" * 42000
    server.send_to(server.clients[fd1].sock, "hey")
    server.select()
    server.send_to(server.clients[fd2].sock, "ola")
    server.select()
    assert client1.recv() == "hey"
    assert client2.recv() == "ola"
    del client1
    server.select()
    del server
    del client2
