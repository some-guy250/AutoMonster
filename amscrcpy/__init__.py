"""amscrcpy: a vendored scrcpy 4.1 client for AutoMonster.

Replaces the old PyPI ``scrcpy-client`` (pinned to the scrcpy 1.20 server). It
ships the official scrcpy 4.1 server jar and supports Android 5.0 (API 21)
through 16 (API 36). Self-contained: imports only ``adbutils``, ``av`` and the
standard library.
"""

from . import protocol
from .client import Client, ControlSender

# Touch actions.
ACTION_DOWN = protocol.ACTION_DOWN
ACTION_UP = protocol.ACTION_UP
ACTION_MOVE = protocol.ACTION_MOVE

# Event names accepted by Client.add_listener / remove_listener.
EVENT_INIT = "init"
EVENT_FRAME = "frame"
EVENT_DISCONNECT = "disconnect"

__all__ = [
    "Client",
    "ControlSender",
    "ACTION_DOWN",
    "ACTION_UP",
    "ACTION_MOVE",
    "EVENT_INIT",
    "EVENT_FRAME",
    "EVENT_DISCONNECT",
]
