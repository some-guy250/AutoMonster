# =============================================================================
# Configurable thresholds, timeouts, and runtime configuration
# =============================================================================

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

# Per-asset gray image overrides (asset_name: use_gray_img)
ASSET_GRAY_IMG = {
    # Box buttons
    "boxspeedup.png": True,
    "boxtounlock.png": True,
    # Cavern icons
    "cavernmisery.png": True,
    "cavernconspiracy.png": True,
    "cavernferal.png": True,
    "cavernhistoria.png": True,
    "cavernmultiverse.png": True,
    "cavernevaris.png": True,
    "caverngeneza.png": True,
    "cavernjestin.png": True,
    "cavernbaba.png": True,
    "cavernkhalorc.png": True,
    "caverntyr.png": True,
    "cavernrobur.png": True,
    "caverntheton.png": True,
    "caverngriffania.png": True,
    "cavernalpine.png": True,
    "cavernabyssal.png": True,
    "caverngalactic.png": True,
    "cavernblossom.png": True,
    "caverndoomed.png": True,
    "cavernmetro.png": True,
    "caverncorrupted.png": True,
    "caverncosmic.png": True,
    "cavernoriginal.png": True,
    # Spin wheel
    "spinwheel.png": True,
    # Team selection
    "selected1.png": True,
    "selected2.png": True,
    "selected3.png": True,
}

# Per-asset threshold overrides (asset_name: threshold)
ASSET_THRESHOLDS = {
    # Slider detection
    "slider.png": SLIDER_THRESHOLD,
    "slider2.png": SLIDER_THRESHOLD,
    # Box buttons
    "boxspeedup.png": BOX_SPEEDUP_THRESHOLD,
    "boxtounlock.png": BOX_SPEEDUP_THRESHOLD,
    # Cavern icons
    "cavernmisery.png": CAVERN_THRESHOLD,
    "cavernconspiracy.png": CAVERN_THRESHOLD,
    "cavernferal.png": CAVERN_THRESHOLD,
    "cavernhistoria.png": CAVERN_THRESHOLD,
    "cavernmultiverse.png": CAVERN_THRESHOLD,
    "cavernevaris.png": CAVERN_THRESHOLD,
    "caverngeneza.png": CAVERN_THRESHOLD,
    "cavernjestin.png": CAVERN_THRESHOLD,
    "cavernbaba.png": CAVERN_THRESHOLD,
    "cavernkhalorc.png": CAVERN_THRESHOLD,
    "caverntyr.png": CAVERN_THRESHOLD,
    "cavernrobur.png": CAVERN_THRESHOLD,
    "caverntheton.png": CAVERN_THRESHOLD,
    "caverngriffania.png": CAVERN_THRESHOLD,
    "cavernalpine.png": CAVERN_THRESHOLD,
    "cavernabyssal.png": CAVERN_THRESHOLD,
    "caverngalactic.png": CAVERN_THRESHOLD,
    "cavernblossom.png": CAVERN_THRESHOLD,
    "caverndoomed.png": CAVERN_THRESHOLD,
    "cavernmetro.png": CAVERN_THRESHOLD,
    "caverncorrupted.png": CAVERN_THRESHOLD,
    "caverncosmic.png": CAVERN_THRESHOLD,
    "cavernoriginal.png": CAVERN_THRESHOLD,
    # Spin wheel
    "spinwheel.png": SPIN_WHEEL_THRESHOLD,
    # Team selection
    "selected1.png": TEAM_SELECTION_THRESHOLD,
    "selected2.png": TEAM_SELECTION_THRESHOLD,
    "selected3.png": TEAM_SELECTION_THRESHOLD,
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
