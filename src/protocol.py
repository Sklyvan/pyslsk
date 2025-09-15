from __future__ import annotations
from typing import Tuple, Any, Dict
import struct
from .constants import (
    MSG_LOGIN,
    MSG_SEARCH_RESULT,
    MSG_SEARCH_REQUEST,
    MSG_DOWNLOAD_REQUEST,
)

# Utility packing functions (placeholder strategy):
# We assume messages: [length:4][code:1][payload...]
# TODO: Confirm actual Soulseek framing.


def pack_message(code: int, payload: bytes) -> bytes:
    length = 1 + len(payload)
    return struct.pack("!I", length) + struct.pack("!B", code) + payload


def pack_string(s: str) -> bytes:
    data = s.encode("utf-8")
    return struct.pack("!H", len(data)) + data  # 2-byte length prefix (placeholder)


def unpack_string(data: bytes, offset: int = 0) -> Tuple[str, int]:
    if offset + 2 > len(data):
        raise ValueError("Not enough data to unpack length")
    (ln,) = struct.unpack_from("!H", data, offset)
    offset += 2
    if offset + ln > len(data):
        raise ValueError("Not enough data to unpack string content")
    s = data[offset : offset + ln].decode("utf-8", errors="replace")
    offset += ln
    return s, offset


def build_login(username: str, password: str) -> bytes:
    # TODO: Replace placeholder login format with real handshake.
    payload = pack_string(username) + pack_string(password)
    return pack_message(MSG_LOGIN, payload)


def build_search(query: str) -> bytes:
    # TODO: Replace placeholder search payload with real format.
    payload = pack_string(query)
    return pack_message(MSG_SEARCH_REQUEST, payload)


def build_download_request(user: str, remote_path: str) -> bytes:
    # TODO: Replace placeholder file request format with real one.
    payload = pack_string(user) + pack_string(remote_path)
    return pack_message(MSG_DOWNLOAD_REQUEST, payload)


def parse_message(raw: bytes) -> Dict[str, Any]:
    """
    Parse a single complete message frame.
    Returns a dict with code and payload raw for higher-level decoding.
    """
    if len(raw) < 5:
        raise ValueError("Frame too short")
    length = struct.unpack_from("!I", raw, 0)[0]
    code = struct.unpack_from("!B", raw, 4)[0]
    payload = raw[5 : 5 + (length - 1)]
    return {"code": code, "payload": payload}


def iter_frames(buffer: bytearray):
    """
    Generator that yields complete frames from buffer, mutating buffer in-place.
    """
    while True:
        if len(buffer) < 4:
            return
        (length,) = struct.unpack_from("!I", buffer, 0)
        if len(buffer) < 4 + length:
            return
        frame = bytes(buffer[0 : 4 + length])
        del buffer[0 : 4 + length]
        yield frame


def decode_search_result(payload: bytes):
    """
    Placeholder search result decoding.
    Real format likely includes a structured set of entries.

    For demonstration:
    [query_str][user][folder][file_count:1 byte][ repeated file entries:
        [filename][size:4 bytes]
    ]
    """
    try:
        offset = 0
        query, offset = unpack_string(payload, offset)
        user, offset = unpack_string(payload, offset)
        folder, offset = unpack_string(payload, offset)
        if offset >= len(payload):
            raise ValueError("Missing file count")
        file_count = payload[offset]
        offset += 1
        files = []
        for _ in range(file_count):
            name, offset = unpack_string(payload, offset)
            if offset + 4 > len(payload):
                raise ValueError("Missing file size")
            (size,) = struct.unpack_from("!I", payload, offset)
            offset += 4
            files.append({"filename": name, "size": size})
        return {
            "query": query,
            "user": user,
            "folder": folder,
            "files": files,
        }
    except Exception as e:
        raise ValueError(f"Failed to decode search result: {e}") from e
