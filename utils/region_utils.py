# =============================================================================
# Unified region recommendation utility
# =============================================================================
# Single source of truth for determining which Region a coordinate falls into.
# Screen dimensions are set once at startup from the device manager.
# =============================================================================

from config.regions import Region

# Screen dimensions (set at startup from device_manager)
SCREEN_W: int = 1280
SCREEN_H: int = 720


def init(screen_w: int, screen_h: int) -> None:
    """Update screen dimensions at startup."""
    global SCREEN_W, SCREEN_H
    SCREEN_W = screen_w
    SCREEN_H = screen_h

# Map bitmask -> exact Region constant name (for composite regions)
_BITMASK_TO_NAME = {
    Region.TOP: "TOP",
    Region.BOTTOM: "BOTTOM",
    Region.LEFT: "LEFT",
    Region.RIGHT: "RIGHT",
    Region.TOP | Region.LEFT: "TOP_LEFT",
    Region.TOP | Region.RIGHT: "TOP_RIGHT",
    Region.BOTTOM | Region.LEFT: "BOTTOM_LEFT",
    Region.BOTTOM | Region.RIGHT: "BOTTOM_RIGHT",
}


def recommend_region(x: int, y: int, w: int = 0, h: int = 0) -> str:
    """Recommend a Region string based on asset position.

    Uses the **center** of the asset to determine the quadrant.
    Screen dimensions are read from module-level SCREEN_W/SCREEN_H (set at startup via init()).

    Returns
    -------
    str
        e.g. ``"Region.BOTTOM_LEFT"``, ``"Region.ALL"``
    """
    center_x = x + w / 2
    center_y = y + h / 2

    r = 0
    if center_y < SCREEN_H / 2:
        r |= Region.TOP
    else:
        r |= Region.BOTTOM
    if center_x < SCREEN_W / 2:
        r |= Region.LEFT
    else:
        r |= Region.RIGHT

    if r == 0:
        return "Region.ALL"

    name = _BITMASK_TO_NAME[r]
    return f"Region.{name}"


def format_region_display(region_str: str) -> str:
    """Convert a Region string to a display-friendly label.

    ``"Region.BOTTOM_LEFT"`` -> ``"BottomLeft"``
    ``"Region.ALL"``         -> ``"All"``
    """
    if region_str == "Region.ALL":
        return "All"
    # Strip "Region.", split on "_", title-case each part, rejoin
    return "".join(part.title() for part in region_str.replace("Region.", "").split("_"))
