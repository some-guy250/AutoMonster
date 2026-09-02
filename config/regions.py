# =============================================================================
# Region definitions for template matching regions.
#
# A Region is a bitmask describing where on the screen an asset is searched
# for. Per-asset region/threshold/gray assignments live in
# ``utils/asset_registry.py`` (the AssetSpec registry); this module only holds
# the Region concept itself.
# =============================================================================


class Region:
    ALL = 0
    TOP = 1
    BOTTOM = 2
    LEFT = 4
    RIGHT = 8
    AD_AREA = 16

    # Combinations
    TOP_LEFT = TOP | LEFT
    TOP_RIGHT = TOP | RIGHT
    BOTTOM_LEFT = BOTTOM | LEFT
    BOTTOM_RIGHT = BOTTOM | RIGHT


# Ads are detected in the two top corners of the screen.
AD_REGION = Region.AD_AREA
