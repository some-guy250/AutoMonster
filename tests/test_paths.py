"""Tests for the centralized dev/frozen path helpers."""

import os
import sys
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils import paths  # noqa: E402


class TestPaths(unittest.TestCase):
    def test_not_frozen_in_dev(self) -> None:
        self.assertFalse(paths.is_frozen())

    def test_project_root_contains_repo_dirs(self) -> None:
        root = paths.project_root()
        self.assertTrue((root / "config").is_dir())
        self.assertTrue((root / "assets").is_dir())
        self.assertTrue((root / "utils").is_dir())

    def test_sc_dir_is_under_root(self) -> None:
        self.assertEqual(paths.sc_dir(), paths.project_root() / "sc")

    def test_resource_path_dev_is_relative(self) -> None:
        # In dev the resource is referenced cwd-relative (original behavior).
        self.assertEqual(paths.resource_path("changelog.json"), Path("changelog.json"))


if __name__ == "__main__":
    unittest.main()
