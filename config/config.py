# =============================================================================
# Configurable thresholds, timeouts, and runtime configuration
# =============================================================================

from enum import Enum
from pathlib import Path

from utils.paths import resource_path

# Default template matching threshold (0.0 to 1.0)
# Higher = more strict matching, Lower = more lenient
DEFAULT_TEMPLATE_THRESHOLD = 0.85

# Named per-asset threshold constants, referenced by the AssetSpec registry
# in utils/asset_registry.py. (Box speedup, spin wheel and team selection use
# the DEFAULT_TEMPLATE_THRESHOLD, so they need no constant.)
SLIDER_THRESHOLD = 0.8    # Slider detection needs a lower threshold
CAVERN_THRESHOLD = 0.75   # Cavern dungeon icons
RUNE_THRESHOLD = 0.93     # Rune assets are very small and similar, need a strict threshold

# Battle timeout in seconds (how long to wait before assuming battle is stuck)
BATTLE_TIMEOUT_SECONDS = 600    # 10 minutes default

# Slider retry limit before asking user for help
SLIDER_MAX_RETRIES = 55

# =============================================================================
# Game Resolution Constants
# =============================================================================

# Target game resolution (landscape)
GAME_WIDTH = 1280
GAME_HEIGHT = 720

# Recommended device resolution
# Android API level bounds supported by the scrcpy server we ship (amscrcpy bundles the
# official scrcpy 4.1 server, which runs on Android 5.0 through 16 and is not yet
# compatible with Android 17+)
MIN_ANDROID_SDK = 21  # Android 5.0, official scrcpy minimum
MAX_ANDROID_SDK = 36  # Android 16, scrcpy 4.1 server does not start on Android 17+ yet

RECOMMENDED_WIDTH = 1280
RECOMMENDED_HEIGHT = 720

# Default device resolution (used as fallback)
DEFAULT_DEVICE_WIDTH = 1080
DEFAULT_DEVICE_HEIGHT = 1920

# =============================================================================
# Image Similarity Threshold
# =============================================================================

# Images must be >98% similar to be considered identical
IMAGE_SIMILARITY_THRESHOLD = 0.98

# =============================================================================
# Swipe Coordinates (as fractions of screen height)
# =============================================================================

# Unlock swipe: start at 85% from top, end at 15% from top
SWIPE_START_Y_FRACTION = 0.85
SWIPE_END_Y_FRACTION = 0.15

# Scroll start position (as fraction of screen height)
SCROLL_START_Y_FRACTION = 0.55

# =============================================================================
# Changelog (version-specific update messages)
# =============================================================================
# JSON file with version -> message mapping. Shown in popup when the app
# launches after a new version is installed. ONLY the user may edit this.
# Add new entries as you release versions. Keep old entries for history.
CHANGELOG_FILE = "changelog.json"

def changelog_path() -> Path:
    """Where to read changelog.json from (see utils.paths.resource_path).

    Frozen exe: embedded via --add-data and extracted to the temp bundle, so
    each released exe carries its own version's entry. Dev: the repo file.
    """
    return resource_path(CHANGELOG_FILE)


# =============================================================================
# Close Game actions
# =============================================================================
class CloseAction(Enum):
    """What to do after closing the game. Values are the user-facing labels."""

    GAME_ONLY = "Close Game Only"
    EXIT_PROGRAM = "Close Game & Exit Program"
    SHUTDOWN = "Close Game & Shutdown Computer"

    @classmethod
    def from_display(cls, text: str) -> "CloseAction":
        for member in cls:
            if member.value == text:
                return member
        raise ValueError(f"Unknown close action: {text}")
