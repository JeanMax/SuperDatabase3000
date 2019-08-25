"""
This module defines a packet structure
(composed of: canari, payload, payload_size, and eventually an extra payload).
You'll find a 'pack' functions allowing you to create a packet
from a payload (btyes object) you want to send, and an 'unpack' function
that can extract a payload from a packet (as a bytes object too) after
validating the packet structure (canari, checksum, length).


packet[64]:    abcd            abcdefghabcdefghabcd        abcdefgh
                 ^               ^                           ^
               canari[4]       checksum[20]                payload_size[8]


                               payload_size
               <------------------------------------------->

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
PAYLOAD_MIN_SIZE = 32  # TODO: tweak me based on DbClient requests size: 256-32
PACKET_MIN_SIZE = (
    CANARI_SIZE + CHECKSUM_SIZE + INT_SIZE
    + PAYLOAD_MIN_SIZE
)  # 64
CHECKSUM_OFFSET = CANARI_SIZE + CHECKSUM_SIZE  # we'll start hasing from there

STRUCT_FORMAT = (
    "!"
    "I"  # canari
    f"{CHECKSUM_SIZE}s"  # checksum
    "Q"  # payload_size
    "{payload_size}s"  # payload: complete its size using format
)


Packet = collections.namedtuple(
    "Packet",
    ["canari", "checksum", "payload_size", "payload"]
)


def _checksum(bytes_buf):
    """Return the sha1 digest of the given 'bytes_buf'."""
    return hashlib.sha1(bytes_buf[CHECKSUM_OFFSET:]).digest()


def _verify_checksum(ctrl_checksum, bytes_buf):
    """
    Return True if the given 'ctrl_checksum' matches the checksum
    of 'bytes_buf', otherwise throw a ValueError.
    """
    if ctrl_checksum != _checksum(bytes_buf):
        raise ValueError("packet: invalid checksum")
    return True


def pack(payload, with_checksum=True):
    """
    Create a packet from the given 'payload' byte object that you want to send.

    If the 'with_checksum' argument is True, the checksum of the payload will
    be calculated and inserted in the packet, otherwise the checksum will be
    set to zeros.
    Returns a bytes object of the created packet (ready to send).
    """

    packet = Packet(
        canari=CANARI,
        checksum=b"\x00" * CHECKSUM_SIZE,
        payload_size=len(payload),
        payload=payload.ljust(PAYLOAD_MIN_SIZE, b"\x00")
    )
    payload_size = max(packet.payload_size, PAYLOAD_MIN_SIZE)
    try:
        bytes_buf = struct.pack(
            STRUCT_FORMAT.format(payload_size=payload_size),
            *packet
        )
    except struct.error as e:
        raise ValueError(f"packet: {e}")

    if with_checksum:
        packet = packet._replace(checksum=_checksum(bytes_buf))
        bytes_buf = struct.pack(
            STRUCT_FORMAT.format(payload_size=payload_size),
            *packet
        )

    return bytes_buf


def unpack(bytes_buf, with_checksum=True):
    """
    Extract the payload (as a bytes object) from the given 'bytes_buf' packet.

    If the 'with_checksum' argument is True, the checksum in the packet will be
    checked against a calculated checksum of the packet payload. Otherwise it
    will just be ignored.
    Returns a bytes object of the extracted payload.
    A ValueError will be thrown if an invalid packet is given as 'bytes_buf'
    (invalid canari, checksum, payload length)
    """

    # first, we try to unpack as if it was a 64 bytes packet
    try:
        packet = struct.unpack(
            STRUCT_FORMAT.format(payload_size=PAYLOAD_MIN_SIZE),
            bytes_buf[:PACKET_MIN_SIZE]
        )
    except struct.error as e:
        raise ValueError(f"packet: {e}")
    packet = Packet(*packet)
    if packet.canari != CANARI:
        raise ValueError("packet: the canari is dead")

    # payload can fit in a 64 bytes packet: just verify checksum, then job done
    if packet.payload_size <= PAYLOAD_MIN_SIZE:
        if with_checksum:
            _verify_checksum(packet.checksum, bytes_buf)
        packet = packet._replace(
            payload=packet.payload[:packet.payload_size]
        )
        return packet

    # packet is actually bigger than 64 bytes (extra_payload)
    if len(bytes_buf) <= PACKET_MIN_SIZE:
        return packet  # the payload is incomplete, and checksum not verified
    try:
        packet = struct.unpack(
            STRUCT_FORMAT.format(payload_size=packet.payload_size),
            bytes_buf
        )
    except struct.error as e:
        raise ValueError(f"packet: {e}")
    packet = Packet(*packet)
    if with_checksum:
        _verify_checksum(packet.checksum, bytes_buf)
    return packet  # complete packet with extra payload
