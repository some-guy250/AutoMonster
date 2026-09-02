"""amscrcpy: a small, self-contained scrcpy 4.1 client for AutoMonster.

Replaces the old PyPI ``scrcpy-client`` (pinned to the scrcpy 1.20 server, which
does not start on Android 15+) with a vendored client that speaks the scrcpy 4.1
protocol and ships the official 4.1 server jar. It supports Android 5.0 (API 21)
through 16 (API 36).

This package is trimmed to what AutoMonster actually uses: screen streaming into
``last_frame`` plus multi-touch control. It imports only ``adbutils``, ``av`` and
the standard library.

Usage:

    client = amscrcpy.Client(max_fps=10, stay_awake=True, device=<adbutils AdbDevice>)
    client.start(threaded=True, daemon_threaded=True)
    frame = client.last_frame          # Optional[np.ndarray] BGR, newest full frame
    w, h = client.resolution           # (width, height), valid after start
    client.control.touch(x, y, amscrcpy.ACTION_DOWN, touch_id=0)
    client.stop()
"""

import os
import socket
import struct
import sys
import threading
import time
from typing import Any, Callable, Optional, Tuple, Union

import numpy as np
from adbutils import AdbDevice, AdbError, Network
from av.codec import CodecContext

from . import protocol


def _jar_path() -> str:
    """Where the scrcpy server jar lives.

    Dev: the jar is committed alongside this package. Frozen exe: the jar is
    embedded with --add-data and extracted into the temp bundle, so it sits in
    the ``amscrcpy`` folder of ``sys._MEIPASS`` (the same place the frozen
    package itself is loaded from). This must not rely on ``__file__`` when
    frozen, for the same reason config.changelog_path() uses ``sys._MEIPASS``.
    """
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "amscrcpy", protocol.SERVER_JAR_FILENAME)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), protocol.SERVER_JAR_FILENAME)


_JAR_PATH = _jar_path()

# Streaming defaults. AutoMonster streams at full resolution and does not need to
# tune these, so they are not exposed as parameters.
_DEFAULT_BITRATE = 8000000
_MAX_SIZE = 0  # 0 = no downscaling


class ControlSender:
    """Sends touch control messages to the device over the control socket."""

    def __init__(self, parent: "Client") -> None:
        self.parent = parent
        self._lock = threading.Lock()

    def touch(
        self,
        x: int,
        y: int,
        action: int = protocol.ACTION_DOWN,
        touch_id: int = 0,
    ) -> None:
        """Inject a finger touch event.

        Args:
            x: horizontal position, device physical pixels.
            y: vertical position, device physical pixels.
            action: amscrcpy.ACTION_DOWN | ACTION_MOVE | ACTION_UP.
            touch_id: stable id for this finger. Use distinct ids (e.g. 1 and 2)
                for simultaneous multi-touch; 0 is fine for a single tap. Do not
                use -1 (the server reserves it for the mouse pointer).
        """
        if not self.parent.alive:
            raise RuntimeError("client is not running, call start() before touch()")
        resolution = self.parent.resolution
        if resolution is None:
            raise RuntimeError("resolution is not available yet, wait for the first frame")
        x, y = max(int(x), 0), max(int(y), 0)
        message = protocol.encode_touch(
            x=x,
            y=y,
            action=action,
            pointer_id=int(touch_id),
            screen_width=resolution[0],
            screen_height=resolution[1],
        )
        control_socket = self.parent._get_control_socket()
        with self._lock:
            control_socket.sendall(message)

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_step_length: int = 5,
        move_steps_delay: float = 0.005,
    ) -> None:
        """Swipe on screen (touch-simulated: DOWN, paced MOVEs, then UP).

        Matches the old scrcpy-client ``swipe`` signature and pacing so existing
        callers behave identically.

        Args:
            start_x: start horizontal position.
            start_y: start vertical position.
            end_x: end horizontal position.
            end_y: end vertical position.
            move_step_length: pixels moved per step (must be >= 1).
            move_steps_delay: seconds to sleep after each step.
        """
        if move_step_length < 1:
            raise ValueError("move_step_length must be >= 1")
        resolution = self.parent.resolution
        if resolution is None:
            raise RuntimeError("resolution is not available yet, wait for the first frame")

        start_x, start_y = int(start_x), int(start_y)
        end_x, end_y = int(end_x), int(end_y)
        if end_x > resolution[0]:
            end_x = resolution[0]
        if end_y > resolution[1]:
            end_y = resolution[1]

        self.touch(start_x, start_y, protocol.ACTION_DOWN)
        next_x, next_y = start_x, start_y
        decrease_x = start_x > end_x
        decrease_y = start_y > end_y
        while True:
            if decrease_x:
                next_x -= move_step_length
                if next_x < end_x:
                    next_x = end_x
            else:
                next_x += move_step_length
                if next_x > end_x:
                    next_x = end_x
            if decrease_y:
                next_y -= move_step_length
                if next_y < end_y:
                    next_y = end_y
            else:
                next_y += move_step_length
                if next_y > end_y:
                    next_y = end_y

            self.touch(next_x, next_y, protocol.ACTION_MOVE)
            if next_x == end_x and next_y == end_y:
                self.touch(next_x, next_y, protocol.ACTION_UP)
                break
            time.sleep(move_steps_delay)


class Client:
    """A scrcpy 4.1 screen-streaming and touch-control client for one device."""

    def __init__(
        self,
        device: Optional[Union[AdbDevice, str]] = None,
        max_fps: int = 0,
        stay_awake: bool = False,
        block_frame: bool = False,
        connection_timeout: int = 3000,
        max_reconnect_attempts: int = 10,
    ) -> None:
        """Create a client. It does not start until you call :meth:`start`.

        Args:
            device: an ``adbutils`` AdbDevice, a serial string, or None (first device).
            max_fps: max streamed frame rate, 0 = unlimited.
            stay_awake: keep the device screen awake while streaming.
            block_frame: accepted for API compatibility; decoded frames are always
                non-empty, so it has no effect here.
            connection_timeout: how long (ms) to wait for the server socket.
            max_reconnect_attempts: if the stream drops while running, how many times to
                re-deploy the server and reconnect before giving up. Default 10 (a fail-fast
                window of a few tens of seconds). 0 means keep reconnecting indefinitely
                until the device is unplugged or stop() is called.
        """
        if max_fps < 0:
            raise ValueError("max_fps must be >= 0")
        if connection_timeout < 0:
            raise ValueError("connection_timeout must be >= 0")
        if max_reconnect_attempts < 0:
            raise ValueError("max_reconnect_attempts must be >= 0")

        if device is None:
            from adbutils import adb
            device = adb.device_list()[0]
        elif isinstance(device, str):
            from adbutils import adb
            device = adb.device(serial=device)

        self.device = device
        self.max_fps = max_fps
        self.stay_awake = stay_awake
        self.block_frame = block_frame
        self.connection_timeout = connection_timeout
        self.max_reconnect_attempts = max_reconnect_attempts

        # Public state.
        self.last_frame: Optional[np.ndarray] = None
        self.resolution: Optional[Tuple[int, int]] = None
        self.device_name: Optional[str] = None
        self.alive = False
        self.control = ControlSender(self)
        self.listeners = {"frame": [], "init": [], "disconnect": []}

        # Sockets / handles, set by start(), cleared by stop().
        self.control_socket: Optional[socket.socket] = None
        self._video_socket: Optional[socket.socket] = None
        self._server_stream = None
        self._stream_thread: Optional[threading.Thread] = None
        self._control_thread: Optional[threading.Thread] = None
        self._stdout_thread: Optional[threading.Thread] = None

    # -- public lifecycle -------------------------------------------------

    def start(self, threaded: bool = False, daemon_threaded: bool = False) -> None:
        """Push the server, open the tunnel and start streaming.

        Args:
            threaded: run the stream loop on a background thread.
            daemon_threaded: run that thread as a daemon (exits with the process).
        """
        if self.alive:
            raise RuntimeError("client is already running")
        self.alive = True
        try:
            # The first session is established synchronously so a connection failure
            # (e.g. an unsupported Android version) raises to the caller immediately.
            self._setup_session()
        except Exception:
            self.alive = False
            self._teardown_session()
            raise
        self._send_to_listeners("init")

        if threaded or daemon_threaded:
            self._stream_thread = threading.Thread(
                target=self._stream_loop, name="amscrcpy-stream", daemon=daemon_threaded
            )
            self._stream_thread.start()
        else:
            self._stream_loop()

    def stop(self) -> None:
        """Stop streaming and clean up sockets, threads and the on-device server."""
        self.alive = False
        current = threading.current_thread()
        # Close the sockets directly (never joins the control/stdout threads, which
        # the stream loop may be re-creating while reconnecting). Closing the sockets
        # unblocks the drain threads and the video read, letting the stream loop
        # finish and run its own teardown. Never join the current thread: stop() may
        # be called from the stream loop itself (inline, non-threaded mode).
        for sock in (self.control_socket, self._video_socket):
            if sock is not None:
                try:
                    sock.close()
                except OSError:
                    pass
        if self._server_stream is not None:
            try:
                self._server_stream.close()
            except Exception:
                pass
        # Give the stream thread a brief chance to run its teardown, but do NOT wait
        # long. On Windows, closing the video socket from this thread does not
        # reliably unblock the blocking recv() the stream thread is parked in, so a
        # long join (it used to be 3s) just stalls the UI on close for nothing: the
        # thread is a daemon (killed on process exit) and the on-device server is
        # already stopped by the adb-stream close above.
        if (
            self._stream_thread is not None
            and self._stream_thread is not current
            and self._stream_thread.is_alive()
        ):
            self._stream_thread.join(timeout=0.5)
        self.control_socket = None
        self._video_socket = None
        self._server_stream = None
        self._stream_thread = None
        self._control_thread = None
        self._stdout_thread = None

    # -- listeners --------------------------------------------------------

    def add_listener(self, event: str, callback: Callable[..., Any]) -> None:
        """Register ``callback`` for an event: 'init', 'frame' or 'disconnect'.

        'frame' callbacks receive the newest BGR frame as a numpy array.
        """
        self.listeners[event].append(callback)

    def remove_listener(self, event: str, callback: Optional[Callable[..., Any]] = None) -> None:
        """Remove a listener for an event.

        With no ``callback``, removes every listener registered for ``event``
        (this is what the app's cleanup does); otherwise removes that one.
        """
        if callback is None:
            self.listeners[event] = []
        else:
            self.listeners[event].remove(callback)

    def _send_to_listeners(self, event: str, *args: Any) -> None:
        for callback in list(self.listeners[event]):
            callback(*args)

    # -- server deploy ----------------------------------------------------

    def _deploy_server(self) -> None:
        """Push the server jar and start it via app_process."""
        if not os.path.isfile(_JAR_PATH):
            raise FileNotFoundError(
                f"scrcpy server jar not found at {_JAR_PATH}. The amscrcpy package is incomplete."
            )
        # Kill any stale server (left over from a previous run or a dropped connection)
        # so the new one can bind the 'scrcpy' abstract socket cleanly.
        try:
            self.device.shell("pkill -f scrcpy")
        except Exception:
            pass
        time.sleep(0.3)
        self.device.sync.push(_JAR_PATH, f"/data/local/tmp/{protocol.ON_DEVICE_JAR_NAME}")

        commands = [
            f"CLASSPATH=/data/local/tmp/{protocol.ON_DEVICE_JAR_NAME}",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            protocol.SCRCPY_VERSION,
            "log_level=info",
            "video=true",
            "audio=false",
            "video_codec=h264",
            f"video_bit_rate={_DEFAULT_BITRATE}",
            f"max_fps={self.max_fps}",
            f"max_size={_MAX_SIZE}",
            "control=true",
            "display_id=0",
            "show_touches=false",
            f"stay_awake={'true' if self.stay_awake else 'false'}",
            "tunnel_forward=true",
            "power_off_on_close=false",
            "clipboard_autosync=false",
            "cleanup=true",
            "send_device_meta=true",
            "send_frame_meta=true",
            "send_dummy_byte=true",
            "send_stream_meta=true",
        ]
        self._server_stream = self.device.shell(commands, stream=True)
        # Drain the server stdout in the background so the pipe never fills and
        # blocks the server. Startup and error lines are printed for debugging.
        self._stdout_thread = threading.Thread(
            target=self._drain_server_stdout, name="amscrcpy-server-stdout", daemon=True
        )
        self._stdout_thread.start()

    # -- tunnel + handshake ------------------------------------------------

    def _init_server_connection(self) -> None:
        """Open the video and control sockets and read the stream meta."""
        self._video_socket = self._connect_retry()
        dummy = self._recv_exact(self._video_socket, 1)
        if dummy != protocol.DUMMY_BYTE:
            raise ConnectionError(f"Did not receive the expected dummy byte (got {dummy!r})")

        # Second connection to the same abstract socket is the control socket.
        self.control_socket = self._connect_retry()

        self.device_name = self._recv_exact(self._video_socket, protocol.DEVICE_NAME_SIZE).decode(
            "utf-8", errors="replace"
        ).rstrip("\x00")
        if not self.device_name:
            raise ConnectionError("Did not receive a device name")

        (codec_id,) = struct.unpack(">I", self._recv_exact(self._video_socket, 4))
        if codec_id == protocol.CODEC_ID_STREAM_DISABLED:
            raise ConnectionError("The device disabled the video stream")
        if codec_id == protocol.CODEC_ID_STREAM_ERROR:
            raise ConnectionError("The device reported a video stream configuration error")
        if codec_id != protocol.CODEC_ID_H264:
            raise ConnectionError(f"Unexpected video codec id 0x{codec_id:08x} (expected H.264)")

        # The first video header must be a session packet carrying the size.
        header = self._recv_exact(self._video_socket, protocol.VIDEO_HEADER_SIZE)
        if not protocol.is_session_header(header):
            raise ConnectionError("Expected the first video packet to be a session header")
        width, height = protocol.parse_session_header(header)
        if width == 0 or height == 0:
            raise ConnectionError(f"Invalid video size {width}x{height}")
        self.resolution = (width, height)

    def _connect_retry(self) -> socket.socket:
        """Connect to the device's abstract 'scrcpy' socket, retrying for the
        configured timeout while the server finishes starting up."""
        attempts = max(1, self.connection_timeout // 100)
        for _ in range(attempts):
            try:
                return self.device.create_connection(
                    Network.LOCAL_ABSTRACT, protocol.SOCKET_NAME
                )
            except AdbError:
                time.sleep(0.1)
        raise ConnectionError(
            "Failed to connect to the scrcpy server. It may not have started; "
            "check that the device is running and try again."
        )

    # -- background loops -------------------------------------------------

    def _drain_server_stdout(self) -> None:
        stream = self._server_stream
        pending = b""
        try:
            while stream is not None and not stream.closed:
                # recv() returns as soon as any bytes are available. read() would
                # instead block until a full chunk OR the stream closes, which held
                # the server's short startup lines until it exited (so they printed
                # at the end of the session instead of at start).
                chunk = stream.recv(1024)
                if not chunk:
                    break
                pending += chunk
                while b"\n" in pending:
                    line, pending = pending.split(b"\n", 1)
                    text = line.decode("utf-8", errors="replace").strip()
                    if text:
                        print(f"[amscrcpy server] {text}", flush=True)
            # Flush any trailing data that had no final newline.
            if pending:
                text = pending.decode("utf-8", errors="replace").strip()
                if text:
                    print(f"[amscrcpy server] {text}", flush=True)
        except Exception:
            pass

    def _stream_loop(self) -> None:
        """Stream, reconnecting automatically if the video socket drops."""
        while self.alive:
            self._run_video_stream()
            if not self.alive:
                break
            print("[amscrcpy] stream dropped, reconnecting...", flush=True)
            self._send_to_listeners("disconnect")
            if not self._reconnect():
                break
        self._teardown_session()

    def _run_video_stream(self) -> None:
        """Read and decode video until the socket drops or stop() is called."""
        codec: Optional[CodecContext] = None
        config_buf = b""
        pending = b""
        video_socket = self._video_socket
        while self.alive:
            try:
                header = self._recv_exact(video_socket, protocol.VIDEO_HEADER_SIZE)
            except (OSError, ConnectionError):
                break
            if protocol.is_session_header(header):
                width, height = protocol.parse_session_header(header)
                self.resolution = (width, height)
                codec = self._make_codec()
                config_buf = b""
                if pending:
                    self._decode_buffered(codec, pending)
                    pending = b""
                continue
            is_config, _is_key, size = protocol.parse_media_header(header)
            raw = self._recv_exact(video_socket, size)
            if is_config:
                # Buffer the config (SPS/PPS); it is prepended to the next packet.
                config_buf = raw
                continue
            # Prepend the pending config so the first media packet is self-contained.
            pending = pending + config_buf + raw
            config_buf = b""
            if codec is None:
                codec = self._make_codec()
            try:
                self._decode_buffered(codec, pending)
                pending = b""
            except Exception as exc:  # a bad packet must not kill the stream
                pending = b""
                print(f"[amscrcpy] decode error (ignored): {exc}", flush=True)

    # -- session setup / teardown -----------------------------------------

    def _setup_session(self) -> None:
        """Deploy the server, open the sockets, read the meta and start the drains."""
        self._deploy_server()
        self._init_server_connection()
        # Keep the control socket healthy by draining any device->client messages.
        # With clipboard_autosync disabled none are expected, but draining is robust
        # against any and prevents the socket read side from ever backing up.
        self._control_thread = threading.Thread(
            target=self._drain_control, name="amscrcpy-control", daemon=True
        )
        self._control_thread.start()

    def _teardown_session(self) -> None:
        """Stop the current session's drain threads and clear the session references."""
        current = threading.current_thread()
        for thread in (self._control_thread, self._stdout_thread):
            if thread is not None and thread is not current and thread.is_alive():
                thread.join(timeout=1.0)
        self._control_thread = None
        self._stdout_thread = None
        self.control_socket = None
        self._video_socket = None
        self._server_stream = None

    def _reconnect(self) -> bool:
        """Re-deploy and reconnect after a drop. Returns True on success."""
        attempt = 0
        while self.alive:
            # If the phone is no longer attached at all, stop trying.
            if not self._device_present():
                print("[amscrcpy] device no longer connected; giving up", flush=True)
                return False
            if self.max_reconnect_attempts > 0 and attempt >= self.max_reconnect_attempts:
                print(f"[amscrcpy] giving up after {attempt} reconnect attempts", flush=True)
                return False
            attempt += 1
            try:
                self._teardown_session()
                self._setup_session()
                print(f"[amscrcpy] reconnected on attempt {attempt}", flush=True)
                return True
            except Exception as exc:
                print(f"[amscrcpy] reconnect attempt {attempt} failed: {exc}", flush=True)
                self._sleep_interruptible(1.0)
        return False

    def _device_present(self) -> bool:
        """Return True if the device is still known to ADB (i.e. not unplugged)."""
        try:
            from adbutils import adb
            return self.device.serial in [d.serial for d in adb.device_list()]
        except Exception:
            return False

    def _sleep_interruptible(self, seconds: float) -> None:
        """Sleep for up to `seconds`, waking early if stop() is called."""
        deadline = time.monotonic() + seconds
        while self.alive:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(0.1, remaining))

    def _get_control_socket(self, timeout: float = 5.0) -> socket.socket:
        """Return the control socket, waiting briefly if a reconnect is in progress."""
        deadline = time.monotonic() + timeout
        while True:
            sock = self.control_socket
            if sock is not None:
                return sock
            if not self.alive:
                raise RuntimeError("client is not running, call start() before touch()")
            if time.monotonic() >= deadline:
                raise RuntimeError("control socket is not connected")
            time.sleep(0.05)

    def _make_codec(self) -> CodecContext:
        return CodecContext.create("h264", "r")

    def _decode_buffered(self, codec: CodecContext, data: bytes) -> None:
        for packet in codec.parse(data):
            for frame in codec.decode(packet):
                frame = frame.to_ndarray(format="bgr24")
                if frame.size == 0:
                    continue
                self.last_frame = frame
                self.resolution = (frame.shape[1], frame.shape[0])
                self._send_to_listeners("frame", frame)

    def _drain_control(self) -> None:
        control_socket = self.control_socket
        if control_socket is None:
            return
        buffer = b""
        while self.alive:
            try:
                chunk = control_socket.recv(65536)
            except OSError:
                break
            if not chunk:
                break
            buffer += chunk
            buffer = self._skip_device_messages(buffer)

    def _skip_device_messages(self, buffer: bytes) -> bytes:
        """Consume complete device messages from the buffer, return the leftover."""
        while buffer:
            try:
                payload_length = protocol.device_message_length(buffer[:1], buffer[1:])
            except ValueError:
                break
            total = 1 + payload_length
            if len(buffer) < total:
                break
            buffer = buffer[total:]
        return buffer

    # -- socket helpers ---------------------------------------------------

    @staticmethod
    def _recv_exact(sock: socket.socket, n: int) -> bytes:
        """Read exactly n bytes from a blocking socket, or raise."""
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = sock.recv(remaining)
            if not chunk:
                raise ConnectionError("video stream disconnected")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)
