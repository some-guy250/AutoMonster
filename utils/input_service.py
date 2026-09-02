"""Low-level device input: raw touches plus the multi-touch gestures the bot uses.

Working in the 1280x720 game space, this service scales coordinates through the
device manager and drives the amscrcpy control sender. Keeping the gesture math
in one place (instead of inlined across the controller) makes it easier to read
and to test.
"""

import time

import amscrcpy

from config.config import GAME_WIDTH, GAME_HEIGHT


class InputService:
    def __init__(self, device_manager):
        self.dm = device_manager

    # -- coordinate scaling (game space -> device pixels) ------------------
    def scale_x(self, x: int) -> int:
        return self.dm.scale_x(x)

    def scale_y(self, y: int) -> int:
        return self.dm.scale_y(y)

    # -- primitive input ----------------------------------------------------
    def touch(self, x: int, y: int, action: int = amscrcpy.ACTION_DOWN, touch_id: int = 0) -> None:
        self.dm.client.control.touch(x, y, action, touch_id=touch_id)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, move_step_length: int = 5, move_steps_delay: float = 0.005) -> None:
        self.dm.client.control.swipe(
            x1, y1, x2, y2,
            move_step_length=move_step_length,
            move_steps_delay=move_steps_delay,
        )

    def tap(self, x: int, y: int, down_pause: float = 0.1) -> None:
        self.touch(x, y, amscrcpy.ACTION_DOWN)
        time.sleep(down_pause)
        self.touch(x, y, amscrcpy.ACTION_UP)

    # -- gestures -----------------------------------------------------------
    def drag(self, x1: int, y1: int, x2: int, y2: int, steps: int = 10, touch_id: int = 1) -> None:
        """Press at (x1, y1), move through ``steps`` interpolated points, lift at (x2, y2)."""
        self.touch(x1, y1, amscrcpy.ACTION_DOWN, touch_id=touch_id)
        time.sleep(0.15)
        for i in range(1, steps + 1):
            x = int(x1 + (x2 - x1) * i / steps)
            y = int(y1 + (y2 - y1) * i / steps)
            self.touch(x, y, amscrcpy.ACTION_MOVE, touch_id=touch_id)
            time.sleep(0.03)
        self.touch(x2, y2, amscrcpy.ACTION_UP, touch_id=touch_id)

    def pinch(self, start_offset: int, end_offset: int, steps: int) -> None:
        """One pinch stage centred on the screen: two fingers move from
        ``start_offset`` to ``end_offset`` (both scaled) over ``steps``."""
        center_x = self.scale_x(GAME_WIDTH // 2)
        center_y = self.scale_y(GAME_HEIGHT // 2)
        start_offset = self.scale_x(start_offset)
        end_offset = self.scale_x(end_offset)

        self.touch(center_x - start_offset, center_y, amscrcpy.ACTION_DOWN, touch_id=1)
        self.touch(center_x + start_offset, center_y, amscrcpy.ACTION_DOWN, touch_id=2)
        time.sleep(0.02)
        for step in range(steps):
            progress = (step + 1) / steps
            if end_offset >= start_offset:
                offset = int(start_offset + (end_offset - start_offset) * progress)
            else:
                offset = int(start_offset - (start_offset - end_offset) * progress)
            self.touch(center_x - offset, center_y, amscrcpy.ACTION_MOVE, touch_id=1)
            self.touch(center_x + offset, center_y, amscrcpy.ACTION_MOVE, touch_id=2)
            time.sleep(0.01)
        self.touch(center_x - end_offset, center_y, amscrcpy.ACTION_UP, touch_id=1)
        self.touch(center_x + end_offset, center_y, amscrcpy.ACTION_UP, touch_id=2)

    def zoom_in(self) -> None:
        """Pinch out (fingers spread) to zoom in: a full 100->300 stage then a
        gentler 100->200 stage."""
        self.pinch(100, 300, 15)
        time.sleep(0.05)
        self.pinch(100, 200, 8)

    def zoom_out(self) -> None:
        """Pinch in (fingers close) to zoom out: a full 300->100 stage then a
        gentler 200->100 stage."""
        self.pinch(300, 100, 15)
        time.sleep(0.05)
        self.pinch(200, 100, 8)
