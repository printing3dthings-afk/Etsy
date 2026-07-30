#!/usr/bin/env python3
"""
Bambu P1S bridge tests (2026-07-30).

Covers the pure/offline-testable pieces of tools/relay/bambu_p1s_bridge.py:
the camera auth packet byte layout (independently verified against a real
open-source reference before it shipped -- see the module's "Camera relay"
comment block for what was checked and how) and the camera frame reader's
desync/oversize handling. Does NOT touch a real printer or MQTT broker --
paho-mqtt itself is only imported lazily inside _build_client() so this file
(and --test-camera/--no-camera) can run without it installed, matching this
repo's pattern of keeping optional/local-only dependencies out of the main
test path (see bambu_requirements.txt vs. requirements.txt).
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sp = str(ROOT / "tools" / "relay")
if sp not in sys.path:
    sys.path.insert(0, sp)

import bambu_p1s_bridge as bridge  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_auth_packet_is_80_bytes_with_verified_layout():
    packet = bridge._build_camera_auth_packet("12345678")
    check(len(packet) == 80, f"expected 80-byte auth packet, got {len(packet)}")
    payload_size, cmd_type, flags, reserved = struct.unpack_from("<IIII", packet, 0)
    check(payload_size == 64, f"expected payload_size=64 (0x40), got {payload_size}")
    check(cmd_type == 0x3000, f"expected type=0x3000, got {hex(cmd_type)}")
    check(flags == 0, f"expected flags=0, got {flags}")
    check(reserved == 0, f"expected reserved=0, got {reserved}")
    username_field = packet[16:48]
    check(username_field == b"bblp".ljust(32, b"\x00"), f"expected 'bblp' null-padded to 32 bytes, got {username_field!r}")
    password_field = packet[48:80]
    check(password_field == b"12345678".ljust(32, b"\x00"), f"expected access code null-padded to 32 bytes, got {password_field!r}")


def test_auth_packet_truncates_long_access_code_instead_of_overflowing():
    long_code = "x" * 40
    packet = bridge._build_camera_auth_packet(long_code)
    check(len(packet) == 80, f"an oversized access code must never grow the packet -- got {len(packet)} bytes")
    password_field = packet[48:80]
    check(password_field == b"x" * 32, "expected the access code truncated to exactly 32 bytes, no padding byte")


class _FakeSocket:
    """Feeds _recv_exact/_read_camera_frames pre-built bytes without a real socket."""
    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0

    def recv(self, n: int) -> bytes:
        chunk = self._data[self._pos:self._pos + n]
        self._pos += len(chunk)
        return chunk

    def close(self):
        pass


def _frame_bytes(payload: bytes, track: int = 0) -> bytes:
    header = struct.pack("<IIII", len(payload), track, 0, 0)
    return header + payload


def test_recv_exact_assembles_chunks_across_multiple_reads():
    sock = _FakeSocket(b"abcdefgh")
    sock.recv = lambda n, _orig=sock.recv: _orig(min(n, 3))  # force multi-chunk assembly
    data = bridge._recv_exact(sock, 8)
    check(data == b"abcdefgh", f"expected reassembled 'abcdefgh', got {data!r}")


def test_recv_exact_raises_on_closed_socket():
    sock = _FakeSocket(b"ab")
    try:
        bridge._recv_exact(sock, 5)
        check(False, "expected ConnectionError when the socket runs out of bytes")
    except ConnectionError:
        pass


def test_read_camera_frames_yields_valid_jpeg_and_stops_on_close():
    jpeg = bridge._JPEG_SOI + b"fake jpeg body" + bridge._JPEG_EOI
    stream = _frame_bytes(jpeg) + _frame_bytes(jpeg)
    sock = _FakeSocket(stream)
    import unittest.mock as mock
    with mock.patch.object(bridge, "_open_camera_socket", return_value=sock):
        received = []
        try:
            bridge._read_camera_frames(received.append)
        except ConnectionError:
            pass  # expected once the fake stream runs dry
        check(len(received) == 2, f"expected 2 frames read before the stream closed, got {len(received)}")
        check(all(f == jpeg for f in received), "every yielded frame must be the exact JPEG bytes sent")


def test_read_camera_frames_drops_desynced_frame_without_crashing():
    jpeg = bridge._JPEG_SOI + b"real jpeg" + bridge._JPEG_EOI
    garbage = b"not a jpeg at all sized to match its own header"
    stream = _frame_bytes(garbage) + _frame_bytes(jpeg)
    sock = _FakeSocket(stream)
    import unittest.mock as mock
    with mock.patch.object(bridge, "_open_camera_socket", return_value=sock):
        received = []
        try:
            bridge._read_camera_frames(received.append)
        except ConnectionError:
            pass
        check(received == [jpeg], f"expected the garbage frame dropped and only the real JPEG yielded, got {received}")


def test_read_camera_frames_rejects_implausible_frame_size():
    # A payload_size larger than _CAMERA_MAX_FRAME_BYTES means the stream is
    # desynced (misread header) -- must raise, never try to recv() gigabytes.
    header = struct.pack("<IIII", bridge._CAMERA_MAX_FRAME_BYTES + 1, 0, 0, 0)
    sock = _FakeSocket(header)
    import unittest.mock as mock
    with mock.patch.object(bridge, "_open_camera_socket", return_value=sock):
        try:
            bridge._read_camera_frames(lambda f: None)
            check(False, "expected ConnectionError for an implausible frame size")
        except ConnectionError:
            pass


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("BAMBU P1S BRIDGE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("BAMBU P1S BRIDGE TESTS OK — camera auth packet layout and frame reader desync/oversize handling behave correctly.")


if __name__ == "__main__":
    run()
