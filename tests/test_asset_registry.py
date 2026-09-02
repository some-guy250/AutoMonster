"""Tests for the unified per-asset template-matching registry."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config.regions import Region  # noqa: E402
from config.config import DEFAULT_TEMPLATE_THRESHOLD  # noqa: E402
from utils.asset_registry import ASSET_SPECS, AssetSpec, get_spec  # noqa: E402


class TestAssetRegistry(unittest.TestCase):
    def test_entries_are_well_formed(self) -> None:
        self.assertGreater(len(ASSET_SPECS), 0)
        for png, spec in ASSET_SPECS.items():
            with self.subTest(asset=png):
                self.assertTrue(png.endswith(".png"), f"{png} is not a png filename")
                self.assertIsInstance(spec, AssetSpec)
                self.assertIsInstance(spec.region, int)
                self.assertIsInstance(spec.threshold, float)
                self.assertIsInstance(spec.gray, bool)
                self.assertGreaterEqual(spec.threshold, 0.0)
                self.assertLessEqual(spec.threshold, 1.0)

    def test_get_spec_returns_default_for_unknown(self) -> None:
        spec = get_spec("not_a_real_asset.png")
        self.assertEqual(spec, AssetSpec())
        self.assertEqual(spec.region, Region.ALL)
        self.assertEqual(spec.threshold, DEFAULT_TEMPLATE_THRESHOLD)
        self.assertFalse(spec.gray)

    def test_get_spec_returns_explicit_entry(self) -> None:
        # slider.png carries a custom threshold in the registry
        self.assertIn("slider.png", ASSET_SPECS)
        spec = get_spec("slider.png")
        self.assertNotEqual(spec.threshold, DEFAULT_TEMPLATE_THRESHOLD)

    def test_region_flags_are_sane(self) -> None:
        # region is a flag field; every entry stores a non-negative int
        for png, spec in ASSET_SPECS.items():
            with self.subTest(asset=png):
                self.assertGreaterEqual(spec.region, 0)


if __name__ == "__main__":
    unittest.main()
