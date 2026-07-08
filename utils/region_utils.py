# =============================================================================
# Unified region recommendation utility
# =============================================================================
# Single source of truth for determining which Region a coordinate falls into
# on the 1280x720 landscape game screen.
# =============================================================================

from config.regions import Region

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
MID_X = SCREEN_WIDTH // 2   # 640
MID_Y = SCREEN_HEIGHT // 2  # 360

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


def recommend_region(
    x: int, y: int, w: int = 0, h: int = 0,
    screen_w: int = SCREEN_WIDTH, screen_h: int = SCREEN_HEIGHT,
) -> str:
    """Recommend a Region string for a match/crop based on its position.

    Uses the **center** of the asset to determine the quadrant.

    Parameters
    ----------
    x, y : int
        Top-left coordinate of the match or crop.
    w, h : int
        Width and height of the asset (0 for crop-only calls where x1/y1/x2/y2
        are already the full bounds).
    screen_w, screen_h : int
        Screen dimensions (defaults to 1280x720).

    Returns
    -------
    str
        e.g. ``"Region.BOTTOM_LEFT"``, ``"Region.ALL"``
    """
    center_x = x + w / 2
    center_y = y + h / 2

    r = 0
    if center_y < screen_h / 2:
        r |= Region.TOP
    else:
        r |= Region.BOTTOM
    if center_x < screen_w / 2:
        r |= Region.LEFT
    else:
        r |= Region.RIGHT

    if r == 0:
        return "Region.ALL"

    # Try exact composite name first
    name = _BITMASK_TO_NAME.get(r)
    if name:
        return f"Region.{name}"

    # Fallback: build composite string
    parts = []
    if r & Region.TOP: parts.append("TOP")
    if r & Region.BOTTOM: parts.append("BOTTOM")
    if r & Region.LEFT: parts.append("LEFT")
    if r & Region.RIGHT: parts.append("RIGHT")
    return " | ".join(f"Region.{p}" for p in parts)


def format_region_display(region_str: str) -> str:
    """Convert a Region string to a display-friendly label.

    ``"Region.BOTTOM_LEFT"`` -> ``"BottomLeft"``
    ``"Region.ALL"``         -> ``"All"``
    """
    if region_str == "Region.ALL":
        return "All"
    # Strip "Region.", split on "_", title-case each part, rejoin
    return "".join(part.title() for part in region_str.replace("Region.", "").split("_"))
