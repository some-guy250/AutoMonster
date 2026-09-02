"""Centralized path helpers for dev vs frozen (PyInstaller) runs.

Previously the "where do my files live?" logic was duplicated across
config.changelog_path and Controller._sc_dir. It lives in one place now.
(The amscrcpy server jar keeps its own path helper: it is package-relative in
dev and must stay self-contained.)
"""

import sys
from pathlib import Path


def is_frozen() -> bool:
    """True when running as a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def resource_path(relative: str) -> Path:
    """Path to an app resource (e.g. changelog.json).

    Frozen: the file is embedded via --add-data and extracted to the temp
    bundle. Dev: the file at the project root (cwd-relative).
    """
    if is_frozen():
        return Path(sys._MEIPASS) / relative
    return Path(relative)


def project_root() -> Path:
    """The directory the app is running from.

    Frozen: the folder containing the exe. Dev: the repo root.
    """
    if is_frozen():
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def sc_dir() -> Path:
    """Where debug screenshots are written (next to the exe or the script)."""
    return project_root() / "sc"
