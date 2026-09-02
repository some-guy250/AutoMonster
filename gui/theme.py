"""Centralized theme tokens (colors + fonts) for the controller GUI.

Previously these were hardcoded as literals across several files; keeping them
here means a visual change is a one-place edit.
"""

FONT_FAMILY = "Arial"


def font(size: int, bold: bool = False) -> tuple:
    """Return a tkinter font tuple using the shared family."""
    return (FONT_FAMILY, size, "bold" if bold else "normal")


# Standard type sizes used across the UI.
FONT_HEADER = font(16, True)
FONT_SUBHEADER = font(14, True)
FONT_NORMAL = font(12)
FONT_BUTTON = font(13, True)
FONT_SMALL = font(11)
FONT_TITLE = font(20, True)

# Colors.
PRIMARY = "#3B8ED0"
PRIMARY_HOVER = "#2d6bb0"
PRIMARY_DARK = "#1F6AA5"

DANGER = "#e74c3c"
DANGER_HOVER = "#c0392b"
SUCCESS = "#2ecc71"
SUCCESS_HOVER = "#27ae60"
WARNING = "#e67e22"
WARNING_HOVER = "#d35400"
ACCENT = "#9b59b6"
ACCENT_HOVER = "#8e44ad"
NEUTRAL = "#95a5a6"
NEUTRAL_HOVER = "#7f8c8d"

# Surfaces / text.
BG = "#2b2b2b"
SURFACE = "#1f1f1f"
SURFACE_ALT = "#2a2a2a"
TEXT = "#ffffff"
TEXT_MUTED = "#cccccc"
