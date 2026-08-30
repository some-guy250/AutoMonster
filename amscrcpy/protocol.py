"""Byte-level scrcpy 4.1 wire protocol: constants, framing, encode/decode.

Every layout here is copied from the official scrcpy v4.1 sources (tag ``v4.1``),
NOT from the old 1.20 Python client. The wire format used below has been stable
since scrcpy 2.0 and is identical in 4.1.

Sources (tag v4.1 of https://github.com/Genymobile/scrcpy):
  - ``app/src/demuxer.c``            video packet/session meta (12-byte header)
  - ``app/src/packet_merger.c``      config packets prepend to the next media packet
  - ``server/.../device/Streamer.java``   server side of the same meta
  - ``app/src/control_msg.c``        control message payload serialization
  - ``server/.../control/ControlMessageReader.java``   control framing (type + fields)
  - ``server/.../control/DeviceMessageWriter.java``    device message framing
  - ``server/.../device/DesktopConnection.java``   dummy byte + device name

The one thing that changed from 1.x to 2.0 is the framing and the 12-byte meta
header. The control message wrapper (1 type byte + fixed-size payload, no length
prefix) is the same in 1.20 and 4.1; only the touch payload layout differs.
"""

import struct

# ---------------------------------------------------------------------------
# Server launch
# ---------------------------------------------------------------------------
# The server rejects a launch line whose version does not match its own
# BuildConfig.VERSION_NAME (Options.parse in the 4.1 jar). Both the version
# string and the jar are 4.1, so they must agree. Kept in one place on purpose.
SCRCPY_VERSION = "4.1"

# The server listens on this local abstract socket when tunnel_forward=true.
# The client (this package) connects to it via adb twice: first connection is
# the video socket, second is the control socket.
SOCKET_NAME = "scrcpy"

# Committed server jar filename inside the package (the official release asset).
SERVER_JAR_FILENAME = "scrcpy-server-v4.1"
# Name the jar is pushed to on the device, and used in the CLASSPATH.
ON_DEVICE_JAR_NAME = "scrcpy-server.jar"

# ---------------------------------------------------------------------------
# Video codec ids (4-byte big-endian ASCII, demuxer.c)
# ---------------------------------------------------------------------------
CODEC_ID_H264 = 0x68323634  # "h264"
CODEC_ID_H265 = 0x68323635  # "h265"
CODEC_ID_AV1 = 0x00617631  # "av1"
CODEC_ID_STREAM_DISABLED = 0  # device explicitly disabled the stream
CODEC_ID_STREAM_ERROR = 1  # stream configuration error on the device

# ---------------------------------------------------------------------------
# Video packet meta flags (top bits of the 8-byte PTS field)
# ---------------------------------------------------------------------------
PACKET_FLAG_SESSION = 1 << 63  # header is a session packet (carries width/height)
PACKET_FLAG_CONFIG = 1 << 62  # header is a config (SPS/PPS) packet
PACKET_FLAG_KEY_FRAME = 1 << 61  # media packet is a key frame

# A video stream is a sequence of 12-byte meta headers. A session header has the
# SESSION bit set and carries the width/height in the last 8 bytes. A media
# header carries (pts | flags) in the first 8 bytes and the packet size in the
# last 4, followed by <size> bytes of raw H.264.
VIDEO_HEADER_SIZE = 12


def is_session_header(header: bytes) -> bool:
    """True when a 12-byte video header is a session (dimension) packet."""
    return bool(header[0] & 0x80)


def parse_session_header(header: bytes) -> tuple:
    """Return (width, height) from a 12-byte session header."""
    width = struct.unpack_from(">I", header, 4)[0]
    height = struct.unpack_from(">I", header, 8)[0]
    return width, height


def parse_media_header(header: bytes) -> tuple:
    """Return (is_config, is_key_frame, packet_size) from a 12-byte media header."""
    pts_flags = struct.unpack_from(">Q", header, 0)[0]
    size = struct.unpack_from(">I", header, 8)[0]
    is_config = bool(pts_flags & PACKET_FLAG_CONFIG)
    is_key = bool(pts_flags & PACKET_FLAG_KEY_FRAME)
    return is_config, is_key, size


# ---------------------------------------------------------------------------
# Device meta (DesktopConnection.sendDeviceMeta)
# ---------------------------------------------------------------------------
# A fixed-length, NUL-terminated device name is written once on the first
# (video) socket, right after the 1-byte dummy.
DEVICE_NAME_SIZE = 64

# The first byte written on the video socket, used to detect a dead tunnel.
DUMMY_BYTE = b"\x00"


# ---------------------------------------------------------------------------
# Control messages (client -> device)
# ---------------------------------------------------------------------------
# Framing is a 1-byte type followed by a fixed-size payload (no length prefix).
# This matches the 1.20 client wrapper; only the touch payload layout is the
# 4.1 one (ControlMessageReader.parseInjectTouchEvent).
CTRL_INJECT_KEYCODE = 0
CTRL_INJECT_TEXT = 1
CTRL_INJECT_TOUCH_EVENT = 2
CTRL_INJECT_SCROLL_EVENT = 3
CTRL_BACK_OR_SCREEN_ON = 4
CTRL_EXPAND_NOTIFICATION_PANEL = 5
CTRL_EXPAND_SETTINGS_PANEL = 6
CTRL_COLLAPSE_PANELS = 7
CTRL_GET_CLIPBOARD = 8
CTRL_SET_CLIPBOARD = 9
CTRL_SET_DISPLAY_POWER = 10
CTRL_ROTATE_DEVICE = 11

# Touch actions (android MotionEvent action mask).
ACTION_DOWN = 0
ACTION_UP = 1
ACTION_MOVE = 2

# A full finger touch is 32 bytes on the wire: type + action + pointer id +
# position (x, y, screen w, screen h) + pressure + action button + buttons.
#   offset 0:  type      u8
#   offset 1:  action    u8
#   offset 2:  pointer_id u64 BE
#   offset 10: x          i32 BE   (device physical pixels)
#   offset 14: y          i32 BE
#   offset 18: screen_w   u16 BE
#   offset 20: screen_h   u16 BE
#   offset 22: pressure   u16 BE   (fixed point, 0x0000..0xFFFF for 0.0..1.0)
#   offset 24: action_btn u32 BE
#   offset 28: buttons    u32 BE
TOUCH_MESSAGE_SIZE = 32

# Pressure is a 16-bit fixed point value: 0xFFFF == full pressure, 0 == none.
PRESSURE_FULL = 0xFFFF
PRESSURE_NONE = 0x0000


def encode_touch(
    x: int,
    y: int,
    action: int,
    pointer_id: int,
    screen_width: int,
    screen_height: int,
) -> bytes:
    """Encode a full 32-byte INJECT_TOUCH_EVENT message.

    ``x``/``y`` are in device physical pixels. For a finger, action_button and
    buttons are 0 (the server forces buttons to 0 for touch and derives the
    down/up state from ``action``). Pressure is full for down/move, none for up.
    """
    if action not in (ACTION_DOWN, ACTION_UP, ACTION_MOVE):
        raise ValueError(f"Invalid touch action: {action!r} (expected 0/1/2)")
    pressure = PRESSURE_NONE if action == ACTION_UP else PRESSURE_FULL
    return struct.pack(
        ">BBqiiHHHiI",
        CTRL_INJECT_TOUCH_EVENT,  # type
        action,
        pointer_id,
        int(x),
        int(y),
        int(screen_width),
        int(screen_height),
        pressure,
        0,  # action button
        0,  # buttons (server forces 0 for touch)
    )


# ---------------------------------------------------------------------------
# Device messages (device -> client)
# ---------------------------------------------------------------------------
# Sent on the control socket. We only drain/ignore them so the socket stays
# healthy. Framing is a 1-byte type + payload (DeviceMessageWriter.write):
#   TYPE_CLIPBOARD:     i32 length + <length> bytes
#   TYPE_ACK_CLIPBOARD: u64 sequence
#   TYPE_UHID_OUTPUT:   u16 id + u16 data length + <length> bytes
DEV_CLIPBOARD = 0
DEV_ACK_CLIPBOARD = 1
DEV_UHID_OUTPUT = 2


def device_message_length(header: bytes, payload: bytes) -> int:
    """Return the number of payload bytes (after the 1 type byte) for a device
    message, given its type byte and the following payload bytes.

    Raises ValueError if the payload is too short to contain the message.
    """
    mtype = header[0]
    if mtype == DEV_CLIPBOARD:
        if len(payload) < 4:
            raise ValueError("CLIPBOARD device message: missing length")
        length = struct.unpack_from(">I", payload, 0)[0]
        return 4 + length
    if mtype == DEV_ACK_CLIPBOARD:
        return 8
    if mtype == DEV_UHID_OUTPUT:
        if len(payload) < 4:
            raise ValueError("UHID_OUTPUT device message: missing length")
        data_length = struct.unpack_from(">H", payload, 2)[0]
        return 2 + 2 + data_length
    raise ValueError(f"Unknown device message type: {mtype!r}")
