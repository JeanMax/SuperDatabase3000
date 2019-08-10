import superdatabase3000.packet as pckt


def test_pack_unpack():
    payload = b"hello"
    bytes_buf = pckt.pack(payload)
    assert len(bytes_buf) == pckt.PACKET_MIN_SIZE
    packet = pckt.unpack(bytes_buf)
    assert packet.payload == payload
    assert packet.payload_size == len(payload)


def test_big_pack_unpack():
    payload = b"hello" * 1000
    bytes_buf = pckt.pack(payload)
    assert len(bytes_buf) > pckt.PACKET_MIN_SIZE
    packet = pckt.unpack(bytes_buf)
    assert packet.payload == payload
    assert packet.payload_size

    packet = pckt.unpack(bytes_buf[:pckt.PACKET_MIN_SIZE])
    assert packet.payload_size == len(payload)
    assert len(packet.payload) == pckt.PAYLOAD_MIN_SIZE
    assert packet.payload == payload[:pckt.PAYLOAD_MIN_SIZE]
