"""Tests for the preview mouse-wheel -> pinch-zoom direction mapping.

``on_preview_scroll`` is pure (reads the event, calls ``gui.queue_zoom``), so it
can be tested headless with a fake gui that records the requested direction.
"""

import os
import sys
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui import gui_events  # noqa: E402


def _make_gui():
    g = types.SimpleNamespace()
    g.zoom_calls = []
    g.queue_zoom = lambda d: g.zoom_calls.append(d)
    return g


class TestPreviewScrollZoom(unittest.TestCase):
    def test_windows_delta_up_is_zoom_in(self) -> None:
        g = _make_gui()
        gui_events.on_preview_scroll(g, types.SimpleNamespace(num=None, delta=120))
        self.assertEqual(g.zoom_calls, ["in"])

    def test_windows_delta_down_is_zoom_out(self) -> None:
        g = _make_gui()
        gui_events.on_preview_scroll(g, types.SimpleNamespace(num=None, delta=-120))
        self.assertEqual(g.zoom_calls, ["out"])

    def test_zero_delta_ignored(self) -> None:
        g = _make_gui()
        gui_events.on_preview_scroll(g, types.SimpleNamespace(num=None, delta=0))
        self.assertEqual(g.zoom_calls, [])

    def test_linux_button4_is_zoom_in(self) -> None:
        g = _make_gui()
        gui_events.on_preview_scroll(g, types.SimpleNamespace(num=4, delta=0))
        self.assertEqual(g.zoom_calls, ["in"])

    def test_linux_button5_is_zoom_out(self) -> None:
        g = _make_gui()
        gui_events.on_preview_scroll(g, types.SimpleNamespace(num=5, delta=0))
        self.assertEqual(g.zoom_calls, ["out"])


if __name__ == "__main__":
    unittest.main()
