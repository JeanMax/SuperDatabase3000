"""
packet[64]:    abcd            abcdefghabcdefghabcd        abcdefgh
                 ^               ^                           ^
               canari[4]       checksum[20]                extra_payload_size[8]



               abcdefghabcdefghabcdefghabcdefgh        [...]
                 ^                                       ^
               payload[32]                             extra_payload
"""

import collections
import struct
import hashlib


CANARI = 0xdeadbeef

CANARI_SIZE = 4  # unsigned int
CHECKSUM_SIZE = 20  # sha1
INT_SIZE = 8  # unsigned long long
PAYLOAD_MIN_SIZE = 32
PACKET_MIN_SIZE = (
    CANARI_SIZE + CHECKSUM_SIZE + INT_SIZE
    + PAYLOAD_MIN_SIZE
)  # 64

STRUCT_FORMAT = (
    "!"
    "I"  # canari
    f"{CHECKSUM_SIZE}s"  # checksum
    "Q"  # extra_payload_size
    f"{PAYLOAD_MIN_SIZE}s"  # payload
)


Packet = collections.namedtuple(
    "Packet",
    ["canari", "checksum", "extra_payload_size", "payload"]
)


def checksum(bytes_buf):
    return hashlib.sha1(bytes_buf[CANARI_SIZE + CHECKSUM_SIZE:]).digest()


def pack(payload):
    payload = payload.zfill(PAYLOAD_MIN_SIZE)
    packet = Packet(
        canari=CANARI,
        checksum=b'0' * CHECKSUM_SIZE,
        extra_payload_size=len(payload) - PAYLOAD_MIN_SIZE,
        payload=payload
    )
    try:
        bytes_buf = struct.pack(STRUCT_FORMAT, *packet)
    except struct.error as e:
        raise ValueError(f"Packet: {e}")
    packet.checksum = checksum(bytes_buf)
    bytes_buf = struct.pack(STRUCT_FORMAT, *packet)
    return bytes_buf


def unpack(bytes_buf):
    try:
        packet = struct.unpack(STRUCT_FORMAT, bytes_buf)
        packet = Packet(*packet)
    except struct.error as e:
        raise ValueError(f"unpack: {e}")
    if packet.canari != CANARI:
        raise ValueError("unpack: the canari is dead")
    if not packet.extra_payload_size and packet.checksum != checksum(bytes_buf):
        raise ValueError("unpack: invalid checksum")
    return packet
