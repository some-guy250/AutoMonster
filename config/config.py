# =============================================================================
# Configurable thresholds, timeouts, and runtime configuration
# =============================================================================

from utils.assets import ASSETS

# Default template matching threshold (0.0 to 1.0)
# Higher = more strict matching, Lower = more lenient
DEFAULT_TEMPLATE_THRESHOLD = 0.85

# Specific thresholds for assets that need different sensitivity
SLIDER_THRESHOLD = 0.8          # Slider detection needs lower threshold
BOX_SPEEDUP_THRESHOLD = 0.85    # Box speedup button detection
CAVERN_THRESHOLD = 0.75         # Cavern dungeon icons
SPIN_WHEEL_THRESHOLD = 0.85     # Spin wheel detection
TEAM_SELECTION_THRESHOLD = 0.85  # Team selection and battle UI detection
RUNE_THRESHOLD = 0.93           # Rune assets are very small and similar, need strict threshold

# Assets that should use grayscale template matching
ASSET_GRAY_IMG = {
    # Box buttons
    ASSETS.BoxSpeedup,
    ASSETS.BoxToUnlock,
    # Cavern icons
    ASSETS.CavernMisery,
    ASSETS.CavernConspiracy,
    ASSETS.CavernFeral,
    ASSETS.CavernHistoria,
    ASSETS.CavernMultiverse,
    ASSETS.CavernEvaris,
    ASSETS.CavernGeneza,
    ASSETS.CavernJestin,
    ASSETS.CavernBaBa,
    ASSETS.CavernKhalorc,
    ASSETS.CavernTyr,
    ASSETS.CavernRobur,
    ASSETS.CavernTheton,
    ASSETS.CavernGriffania,
    ASSETS.CavernAlpine,
    ASSETS.CavernAbyssal,
    ASSETS.CavernGalactic,
    ASSETS.CavernBlossom,
    ASSETS.CavernDoomed,
    ASSETS.CavernMetro,
    ASSETS.CavernCorrupted,
    ASSETS.CavernCosmic,
    ASSETS.CavernOriginal,
    # Spin wheel
    ASSETS.SpinWheel,
    # Team selection
    ASSETS.RankUp1,
    ASSETS.RankUp2,
    ASSETS.RankUp3,
    ASSETS.RankUp4,
    ASSETS.RankUp5,
    ASSETS.RankUp6,
    ASSETS.RankUp1Synergy,
    ASSETS.RankUp2Synergy,
    ASSETS.RankUp3Synergy,
    ASSETS.RankUp4Synergy,
    ASSETS.RankUp5Synergy,
    ASSETS.RankUp6Synergy,
}

# Per-asset threshold overrides (asset_name: threshold)
ASSET_THRESHOLDS = {
    # Slider detection
    ASSETS.Slider: SLIDER_THRESHOLD,
    ASSETS.Slider2: SLIDER_THRESHOLD,
    # Box buttons
    ASSETS.BoxSpeedup: BOX_SPEEDUP_THRESHOLD,
    ASSETS.BoxToUnlock: BOX_SPEEDUP_THRESHOLD,
    # Cavern icons
    ASSETS.CavernMisery: CAVERN_THRESHOLD,
    ASSETS.CavernConspiracy: CAVERN_THRESHOLD,
    ASSETS.CavernFeral: CAVERN_THRESHOLD,
    ASSETS.CavernHistoria: CAVERN_THRESHOLD,
    ASSETS.CavernMultiverse: CAVERN_THRESHOLD,
    ASSETS.CavernEvaris: CAVERN_THRESHOLD,
    ASSETS.CavernGeneza: CAVERN_THRESHOLD,
    ASSETS.CavernJestin: CAVERN_THRESHOLD,
    ASSETS.CavernBaBa: CAVERN_THRESHOLD,
    ASSETS.CavernKhalorc: CAVERN_THRESHOLD,
    ASSETS.CavernTyr: CAVERN_THRESHOLD,
    ASSETS.CavernRobur: CAVERN_THRESHOLD,
    ASSETS.CavernTheton: CAVERN_THRESHOLD,
    ASSETS.CavernGriffania: CAVERN_THRESHOLD,
    ASSETS.CavernAlpine: CAVERN_THRESHOLD,
    ASSETS.CavernAbyssal: CAVERN_THRESHOLD,
    ASSETS.CavernGalactic: CAVERN_THRESHOLD,
    ASSETS.CavernBlossom: CAVERN_THRESHOLD,
    ASSETS.CavernDoomed: CAVERN_THRESHOLD,
    ASSETS.CavernMetro: CAVERN_THRESHOLD,
    ASSETS.CavernCorrupted: CAVERN_THRESHOLD,
    ASSETS.CavernCosmic: CAVERN_THRESHOLD,
    ASSETS.CavernOriginal: CAVERN_THRESHOLD,
    # Spin wheel
    ASSETS.SpinWheel: SPIN_WHEEL_THRESHOLD,
    # Team selection
    ASSETS.RankUpSelected1: TEAM_SELECTION_THRESHOLD,
    ASSETS.RankUpSelected2: TEAM_SELECTION_THRESHOLD,
    ASSETS.RankUpSelected3: TEAM_SELECTION_THRESHOLD,
}

# Battle timeout in seconds (how long to wait before assuming battle is stuck)
BATTLE_TIMEOUT_SECONDS = 600    # 10 minutes default

# Slider retry limit before asking user for help
SLIDER_MAX_RETRIES = 35

# =============================================================================
# Game Resolution Constants
# =============================================================================

# Target game resolution (landscape)
GAME_WIDTH = 1280
GAME_HEIGHT = 720

# Recommended device resolution
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
