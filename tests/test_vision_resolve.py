"""Tests for VisionManager._resolve (per-asset threshold/gray resolution).

``_resolve`` only uses module-level helpers (get_spec + threshold constants),
so we instantiate without running ``__init__`` (which loads templates from disk).
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.config import (  # noqa: E402
    DEFAULT_TEMPLATE_THRESHOLD,
    RUNE_THRESHOLD,
    SLIDER_THRESHOLD,
)
from utils.asset_registry import RUNE_PREFIXES  # noqa: E402
from utils.vision_manager import VisionManager  # noqa: E402


def _bare_vision() -> VisionManager:
    return VisionManager.__new__(VisionManager)


class TestVisionResolve(unittest.TestCase):
    def setUp(self) -> None:
        self.vm = _bare_vision()

    def test_explicit_asset_threshold_wins(self) -> None:
        thr, _ = self.vm._resolve("slider.png", DEFAULT_TEMPLATE_THRESHOLD, False)
        self.assertEqual(thr, SLIDER_THRESHOLD)

    def test_caller_threshold_kept_for_plain_asset(self) -> None:
        # No spec for this asset, so a caller-supplied threshold is preserved.
        thr, gray = self.vm._resolve("plain_button.png", 0.5, False)
        self.assertEqual(thr, 0.5)
        self.assertFalse(gray)

    def test_gray_flag_forced_by_registry(self) -> None:
        # spinwheel.png is flagged gray in the registry.
        _, gray = self.vm._resolve("spinwheel.png", DEFAULT_TEMPLATE_THRESHOLD, False)
        self.assertTrue(gray)

    def test_rune_fallback_only_when_default(self) -> None:
        rune = "rune1LifeS.png"
        self.assertTrue(rune.startswith(RUNE_PREFIXES))
        # default threshold -> strict rune threshold
        thr, _ = self.vm._resolve(rune, DEFAULT_TEMPLATE_THRESHOLD, False)
        self.assertEqual(thr, RUNE_THRESHOLD)
        # explicit caller threshold is never clobbered
        thr2, _ = self.vm._resolve(rune, 0.42, False)
        self.assertEqual(thr2, 0.42)


if __name__ == "__main__":
    unittest.main()
